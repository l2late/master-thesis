"""
Evaluate and compare RBC and MPC controllers, extracting best hopt params
from paired Optuna databases (mpc_tuning_<id> ↔ rbc_tuning_<id>).

Usage
-----
    # Point at a directory containing extracted cloud hopt output:
    uv run python scripts/control/evaluate_rbc_and_mpc.py --hopt-dir output/eval_hopt/

    # Set a target max comfort violation and select trials that satisfy it:
    uv run python scripts/control/evaluate_rbc_and_mpc.py \\
        --hopt-dir output/eval_hopt/ --max-comfort-violation 20

    # Get help:
    uv run python scripts/control/evaluate_rbc_and_mpc.py --help
"""

import argparse
import json
import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
import torch
from optuna.trial import FrozenTrial, TrialState

from alphabuilding import constants as global_config
from alphabuilding.control.brcm_building import (
    BRCMBuildingSimulator,
    test_disturbances,
)
from alphabuilding.control.controllers import EconomicMPCController, RbcController
from alphabuilding.control.model_provision import (
    ModelBundle,
    ModelProvider,
    WandBModelProvider,
)
from alphabuilding.control.performance_metrics import hvac_control_performance_metrics
from alphabuilding.control.simulation import run_simulation
from alphabuilding.control.state_estimation import (
    AugmentedLuenbergerObserver,
    build_augmented_system,
    check_detectability_pbh,
    check_observability,
    conditioning_report,
    design_augmented_gain,
)
from alphabuilding.control.types import SimulationConfig, SimulationPhase
from alphabuilding.control.utils import get_controller_input_df, load_learned_lti_ss
from alphabuilding.control.visualization import (
    plot_observer_convergence,
    plot_simulation_results_multiple_controllers,
)
from alphabuilding.domain.types import Scalers
from alphabuilding.infrastructure.optuna.discovery import find_paired_studies
from alphabuilding.infrastructure.optuna.study_analysis import (
    RankedTrial,
    RankingStrategy,
    controller_params_from_trial,
    get_sorted_best_trials,
)
from alphabuilding.infrastructure.optuna.visualization import (
    MPC_STYLE,
    RBC_STYLE,
    ParetoStudy,
    plot_pareto_dominant,
)
from alphabuilding.utils.logging_config import setup_logging
from alphabuilding.utils.paths import paths

N_ACTUATORS = 5
MAX_RAD_POWER_W_M2 = 35.0

torch.set_grad_enabled(False)


def fmt_duration(seconds: float) -> str:
    """Render *seconds* as ``Hh MMm SS.sss`` plus raw total."""
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}h {int(m):02}m {s:05.2f}s ({seconds:.2f}s total)"


@contextmanager
def timed(label: str):
    """Context manager: prints a formatted wall-clock duration on exit."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"✅  {label} completed in {fmt_duration(elapsed)}")


# ── helpers ──────────────────────────────────────────────────────────────────


def rbc_params_from_trial(
    trial: FrozenTrial,
    *,
    n_actuators: int = N_ACTUATORS,
    u_max_override: float | None = None,
    deadband_override: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Reconstruct RBC controller array params from an Optuna trial.

    The RBC hopt study stores scalar params:
    - ``u_max``      : maximum heating power per actuator (W/m²)
    - ``deadband``   : hysteresis deadband (°C)

    Both are broadcast to ``n_actuators``.

    Optional overrides force a specific value instead of reading the trial.

    Returns
    -------
    u_max : np.ndarray, shape (n_actuators,)
    deadband : np.ndarray, shape (n_actuators,)
    """
    p = trial.params

    if u_max_override is not None:
        u_max = np.ones(n_actuators) * u_max_override
    elif "u_max" in p:
        u_max = np.ones(n_actuators) * p["u_max"]
    else:
        raise KeyError("Trial has no 'u_max' param and no override provided.")

    if deadband_override is not None:
        deadband = np.ones(n_actuators) * deadband_override
    elif "deadband" in p:
        deadband = np.ones(n_actuators) * p["deadband"]
    else:
        raise KeyError("Trial has no 'deadband' param and no override provided.")

    return u_max, deadband


# --------------------------------------------------------------------------- #
#  Performance-summary helpers (console + LaTeX / JSON)
# --------------------------------------------------------------------------- #

# Metric definitions shared by all output formats
METRIC_DEFS = [
    {
        "label": "Energy consumption [W·h]",
        "col": "total_energy_watt_hour",
        "unit": "Wh",
    },
    {
        "label": "Comfort violation [K·h]",
        "col": "total_comfort_violation_kelvin_hours",
        "unit": "K·h",
    },
    {
        "label": "Peak power [W]",
        "col": "max_power_consumption_watt",
        "unit": "W",
    },
]


def _build_metric_summary(
    rbc_perf_row: pd.Series,
    mpc_perf_row: pd.Series,
) -> list[dict]:
    """Build list of dicts with RBC, MPC, and improvement for each metric."""
    summary = []
    for m in METRIC_DEFS:
        rbc_val = float(rbc_perf_row[m["col"]])
        mpc_val = float(mpc_perf_row[m["col"]])
        improvement = (rbc_val - mpc_val) / rbc_val * 100
        summary.append(
            {
                "label": m["label"],
                "col": m["col"],
                "unit": m["unit"],
                "rbc": rbc_val,
                "mpc": mpc_val,
                "improvement_pct": improvement,
            }
        )
    return summary


def _print_metric_table(metric_summary: list[dict]) -> None:
    """Print the performance summary to the console."""
    width = 70
    print("\n" + "━" * width)
    print(f"{'Metric':<28s}  {'RBC':>10s}  {'MPC':>10s}  {'Improvement':>12s}")
    print("─" * width)
    for m in metric_summary:
        sign = "+" if m["improvement_pct"] >= 0 else ""
        unit_str = f"{m['label']} ({m['unit']})"
        print(
            f"{unit_str:<28s}"
            f"  {m['rbc']:>10.2f}  {m['mpc']:>10.2f}"
            f"  {sign}{m['improvement_pct']:>10.2f}%"
        )
    print("━" * width)


def _write_latex_table(metric_summary: list[dict], path: Path) -> Path:
    """Write a complete LaTeX ``table`` environment ready for ``\\input{}``.

    Requires the ``booktabs`` package (``\\usepackage{booktabs}``) in the
    document preamble.
    """

    rows = []
    for m in metric_summary:
        sign = "+" if m["improvement_pct"] >= 0 else ""
        imp_str = f"{sign}{m['improvement_pct']:.1f}"
        rows.append(
            f"  {m['label']} & "
            f"${m['rbc']:.2f}$ & "
            f"${m['mpc']:.2f}$ & "
            f"${imp_str}\\,$\\% \\\\"
        )

    rows_tex = "\n".join(rows)

    tex_content = (
        r"""
    \begin{table}[htbp]
    \centering
    \caption{Performance comparison: RBC vs. MPC}
    \label{tab:controller_performance}
    \begin{tabular}{lrrr}
    \toprule
    \textbf{Metric} & \textbf{RBC} & \textbf{MPC} & \textbf{Improvement $\Delta$} \\
    \midrule
    """
        + rows_tex
        + r"""
    \\
    \bottomrule
    \end{tabular}
    \end{table}
    """
    )

    with open(path, "w") as f:
        f.write(tex_content)
    return path


def _save_metrics_json(
    rbc_perf_row: pd.Series,
    mpc_perf_row: pd.Series,
    metric_summary: list[dict],
    path: Path,
) -> Path:
    """Save raw metrics + improvement as JSON (backwards-compatible)."""

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    perf_json = {
        "rbc": {col: _convert(val) for col, val in rbc_perf_row.items()},
        "mpc": {col: _convert(val) for col, val in mpc_perf_row.items()},
        "comparison": [
            {
                "metric": m["label"],
                "rbc": m["rbc"],
                "mpc": m["mpc"],
                "improvement_pct": m["improvement_pct"],
            }
            for m in metric_summary
        ],
    }
    with open(path, "w") as f:
        json.dump(perf_json, f, indent=2)
    return path


# --------------------------------------------------------------------------- #
#  Optuna helpers
# --------------------------------------------------------------------------- #


def _sorted_best_trial(
    db_path: Path,
    study_name: str,
    *,
    strategy: RankingStrategy = RankingStrategy.WEIGHTED_SUM,
    weights: list[float] | None = None,
) -> RankedTrial:
    """Convenience: fetch the #1 ranked trial from a study."""
    ranked = get_sorted_best_trials(
        study_name=study_name,
        db_path=db_path,
        strategy=strategy,
        weights=weights,
    )
    assert ranked, f"No best trials found in study '{study_name}'"
    return ranked[0]


def _select_under_comfort_cap(
    db_path: Path,
    study_name: str,
    comfort_cap: float,
) -> FrozenTrial | None:
    """Select the lowest-energy trial whose comfort violation ≤ cap.

    Works for both MPC and RBC studies (both are bi-objective: energy, comfort).

    Args:
        db_path: Path to the Optuna SQLite database.
        study_name: Name of the tuning study.
        comfort_cap: Maximum allowed comfort violation in K·h.

    Returns:
        The selected FrozenTrial, or None if no trial satisfies the constraint.
    """
    study = optuna.load_study(
        study_name=study_name,
        storage=f"sqlite:///{db_path}",
    )

    feasible = []
    for t in study.trials:
        if t.state != TrialState.COMPLETE:
            continue
        if t.values is None or len(t.values) < 2:
            continue
        comfort = float(t.values[1])
        if comfort <= comfort_cap:
            feasible.append(t)

    # primary: energy, secondary: comfort, tie-break: trial number
    feasible.sort(key=lambda t: (float(t.values[0]), float(t.values[1]), t.number))
    return feasible[0] if feasible else None


def _count_feasible_trials(
    db_path: Path,
    study_name: str,
    comfort_cap: float,
) -> tuple[int, int]:
    """Return (feasible_count, total_complete_count)."""
    study = optuna.load_study(
        study_name=study_name,
        storage=f"sqlite:///{db_path}",
    )
    total = 0
    feasible = 0
    for t in study.trials:
        if t.state != TrialState.COMPLETE:
            continue
        if t.values is None or len(t.values) < 2:
            continue
        total += 1
        if float(t.values[1]) <= comfort_cap:
            feasible += 1
    return feasible, total


# --------------------------------------------------------------------------- #
#  Model resolution (WandB → local cache, reused by hopt scripts)
# --------------------------------------------------------------------------- #


def resolve_model_provider(
    run_id: str,
    *,
    entity: str,
    project: str,
    download_dir: Path | None = None,
) -> ModelBundle:
    """Resolve model from WandB into the shared artifact cache.

    ``WandBModelProvider`` downloads to ``{cache_dir}/{run_id}/`` which mirrors
    a Hydra run directory.  Subsequent calls for the same ``run_id`` reuse
    the already-cached checkpoint and config — no re-download.
    """
    provider = WandBModelProvider(
        entity=entity,
        project=project,
        run_id=run_id,
        cache_dir=download_dir,
    )
    return provider.provide()


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Evaluate and compare RBC and MPC controllers. "
            "Discovers best hopt params from paired Optuna databases."
        ),
    )
    default_hopt_dir = Path(
        os.environ.get("HOPT_DIR", str(Path(paths.output_dir) / "eval_hopt"))
    )
    p.add_argument(
        "--hopt-dir",
        type=Path,
        default=default_hopt_dir,
        help=(
            "Directory to scan recursively for paired Optuna .db files. "
            "Auto-pairs mpc_tuning_<id> ↔ rbc_tuning_<id> studies and "
            "extracts the best trial params from each. "
            "Default: $HOPT_DIR or output/eval_hopt (relative to project root)."
        ),
    )
    p.add_argument(
        "--max-comfort-violation",
        type=float,
        default=None,
        help=(
            "Target maximum comfort violation in K·h. When set, selects the "
            "lowest-energy RBC and MPC trials whose comfort ≤ this cap. "
            "When omitted, uses the best-ranked (weighted-sum) trial from each study."
        ),
    )

    # ── WandB Model Source ────────────────────────────────────────
    wb = p.add_argument_group("Model source (WandB)")
    wb.add_argument(
        "--entity",
        default=os.environ.get("WANDB_ENTITY"),
        help="WandB entity  (default: $WANDB_ENTITY)",
    )
    wb.add_argument(
        "--project",
        default=os.environ.get("WANDB_PROJECT"),
        help="WandB project  (default: $WANDB_PROJECT)",
    )
    wb.add_argument(
        "--download-dir",
        type=Path,
        default=None,
        help="Local directory to cache WandB artifact downloads "
        "(default: output/artifacts/wandb_cache)",
    )
    return p


def _setup_logging() -> None:
    setup_logging(level=logging.INFO)
    logging.getLogger("alphabuilding.control").setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    _setup_logging()

    # ── 1. Discover paired studies ───────────────────────────────
    paired = find_paired_studies(args.hopt_dir)
    if not paired:
        raise SystemExit(
            f"\nNo paired MPC↔RBC studies found under {args.hopt_dir}. "
            f"Expected study names matching 'mpc_tuning_<id>' and 'rbc_tuning_<id>'."
        )
    p = paired[0]
    print(f"\n🔍  Found paired studies (run_id={p.run_id}):")
    print(f"   MPC study : {p.mpc_study}  (db: {p.mpc_db})")
    print(f"   RBC study : {p.rbc_study}  (db: {p.rbc_db})")

    # ── 2. Resolve model from WandB (reuses existing cache) ──────
    if not args.entity or not args.project:
        raise SystemExit(
            "\nError: --entity and --project are required to resolve the model checkpoint.\n"
            "Set WANDB_ENTITY / WANDB_PROJECT env vars or pass --entity / --project."
        )
    print(f"\n📦  Resolving model from WandB (run_id={p.run_id}) …")
    model_bundle = resolve_model_provider(
        p.run_id,
        entity=args.entity,
        project=args.project,
        download_dir=args.download_dir,
    )
    print(f"   Model checkpoint : {model_bundle.run_dir / 'checkpoints' / 'last.ckpt'}")
    print(f"   Hydra config     : {model_bundle.run_dir / '.hydra' / 'config.yaml'}")

    # ── 3. Load model, plant, observer ───────────────────────────
    sys_learned, dm, Kd_learned, cfg = load_learned_lti_ss(
        path=model_bundle.run_dir,
        auto_select_last=False,
    )

    scalers = Scalers(
        temp=dm.zone_temp_scaler,
        amb=dm.ambient_temp_scaler,
        sol=dm.solar_radiation_scaler,
        heat=dm.heat_input_scaler,
    )

    df = test_disturbances(global_config.BRCM_MAT_FILE, dm)
    controller_input_df = get_controller_input_df(global_config.BRCM_MAT_FILE, dm)

    plant = BRCMBuildingSimulator.from_mat_file(global_config.BRCM_MAT_FILE)

    # MPC Settings
    mpc_horizon_hours = 24
    u_min_W_m2 = np.zeros(N_ACTUATORS)
    u_max_W_m2 = np.ones(N_ACTUATORS) * MAX_RAD_POWER_W_M2

    # Timing
    plant_step_length_seconds = 30
    controller_step_length_seconds = 15 * 60
    controller_steps_per_hour = int(3600 // controller_step_length_seconds)
    assert controller_steps_per_hour == 4
    controller_steps_per_plant_step = (
        controller_step_length_seconds / plant_step_length_seconds
    )

    warm_up_days = 14
    warmup_steps = int(
        warm_up_days * 24 * controller_steps_per_hour * controller_steps_per_plant_step
    )
    eval_days = 7
    eval_steps = int(
        eval_days * 24 * controller_steps_per_hour * controller_steps_per_plant_step
    )

    A = sys_learned.system.A
    B = sys_learned.system.B
    C = sys_learned.system.C
    nd = 5  # input disturbance for rooms
    nx = sys_learned.system.A.shape[0]

    # Observer noise parameters
    std_x_phys = 0.05
    std_d_phys = 0.01
    std_y_phys = 1e-6

    qx_phys = std_x_phys**2
    qd_phys = std_d_phys**2
    ry_phys = std_y_phys**2
    var_scale_factor = scalers.temp.base_scaler.scale_**2
    qx = qx_phys / var_scale_factor
    qd = qd_phys / var_scale_factor
    ry = ry_phys / var_scale_factor

    A_aug, B_aug, C_aug = build_augmented_system(A, B, C, nd)

    conditioning_report(A_aug, C_aug, nd)
    rank, n_aug, is_obs = check_observability(A_aug, C_aug)
    print(f"\nObservability rank: {rank} / {n_aug}  →  fully observable: {is_obs}")
    modes = check_detectability_pbh(A_aug, C_aug)
    if not modes:
        print("DETECTABLE ✓ — augmented observer design is feasible")
    else:
        print(f"WARNING: {len(modes)} undetectable mode(s): {modes}")

    K_aug, Q_aug, R_y = design_augmented_gain(
        A_aug, C_aug, nx=nx, nd=nd, qx=qx, qd=qd, ry=ry
    )
    print(f"K_aug shape: {K_aug.shape}")
    eig_obs = np.linalg.eigvals((np.eye(nx + nd) - K_aug @ C_aug) @ A_aug)
    print(f"eig((I - K C) A) magnitudes: {np.sort(np.abs(eig_obs))[::-1][:10]}")

    observer = AugmentedLuenbergerObserver(
        A_aug=A_aug,
        B_aug=B_aug,
        C_aug=C_aug,
        K_aug=K_aug,
        nx=nx,
        nd=nd,
        x0=plant.x[:nx],
        scalers=scalers,
    )

    simulation_config = SimulationConfig(
        warmup_steps=warmup_steps,
        eval_steps=eval_steps,
    )

    # ── 4. Select RBC and MPC trials ─────────────────────────────
    if args.max_comfort_violation is not None:
        # ── Cap-driven selection ─────────────────────────────────────
        comfort_cap = args.max_comfort_violation
        print(f"\n📏  Target max comfort violation: {comfort_cap:.4f} K·h")

        rbc_trial = _select_under_comfort_cap(
            p.rbc_db, p.rbc_study, comfort_cap=comfort_cap
        )
        if rbc_trial is None:
            raise RuntimeError(
                f"No RBC trial satisfies comfort ≤ {comfort_cap:.4f} K·h. "
                f"Consider increasing the cap or re-running the RBC hopt study."
            )

        mpc_trial = _select_under_comfort_cap(
            p.mpc_db, p.mpc_study, comfort_cap=comfort_cap
        )
        if mpc_trial is None:
            raise RuntimeError(
                f"No MPC trial satisfies comfort ≤ {comfort_cap:.4f} K·h. "
                f"Consider increasing the cap or re-running the MPC hopt study."
            )

        rbc_feasible, rbc_total = _count_feasible_trials(
            p.rbc_db, p.rbc_study, comfort_cap
        )
        mpc_feasible, mpc_total = _count_feasible_trials(
            p.mpc_db, p.mpc_study, comfort_cap
        )

        print("\n🎯  Selected RBC trial (lowest energy under cap):")
        print(f"    Trial #          : {rbc_trial.number}")
        print(f"    Feasible trials  : {rbc_feasible} of {rbc_total}")
        print(f"    Energy  (values[0]): {float(rbc_trial.values[0]):.2f} Wh")
        print(f"    Comfort (values[1]): {float(rbc_trial.values[1]):.4f} K·h")

        print("\n🎯  Selected MPC trial (lowest energy under cap):")
        print(f"    Trial #          : {mpc_trial.number}")
        print(f"    Feasible trials  : {mpc_feasible} of {mpc_total}")
        print(f"    Energy  (values[0]): {float(mpc_trial.values[0]):.2f} Wh")
        print(f"    Comfort (values[1]): {float(mpc_trial.values[1]):.4f} K·h")
    else:
        # ── Default: best-ranked trial from each study ───────────────
        print("\n📏  No comfort cap — selecting best-ranked trials (weighted-sum)")

        rbc_ranked = _sorted_best_trial(p.rbc_db, p.rbc_study)
        rbc_trial = rbc_ranked.trial

        mpc_ranked = _sorted_best_trial(p.mpc_db, p.mpc_study)
        mpc_trial = mpc_ranked.trial

        print("\n🎯  Selected RBC trial (best ranked):")
        print(f"    Trial #          : {rbc_trial.number}  (rank #{rbc_ranked.rank})")
        print(f"    Energy  (values[0]): {float(rbc_trial.values[0]):.2f} Wh")
        print(f"    Comfort (values[1]): {float(rbc_trial.values[1]):.4f} K·h")

        print("\n🎯  Selected MPC trial (best ranked):")
        print(f"    Trial #          : {mpc_trial.number}  (rank #{mpc_ranked.rank})")
        print(f"    Energy  (values[0]): {float(mpc_trial.values[0]):.2f} Wh")
        print(f"    Comfort (values[1]): {float(mpc_trial.values[1]):.4f} K·h")

    # ── 5. Extract controller params from selected trials ────────
    # u_max stays hardcoded at 35 W/m² for both controllers.
    _, rbc_deadband = rbc_params_from_trial(
        rbc_trial, u_max_override=MAX_RAD_POWER_W_M2
    )

    R_weights, slack_weights, margins = controller_params_from_trial(mpc_trial)
    lambda_du = mpc_trial.params.get("lambda_du", 0.0)

    print(f"\n⚙️  RBC deadband : {rbc_deadband[0]:.4f} °C")
    print(f"   R_weight[0]      : {R_weights[0]:.4f}")
    print(f"   slack_weight[0]  : {slack_weights[0]:.4f}")
    print(f"   lambda_du        : {lambda_du:.4f}")
    print(f"   margins          : {margins}")

    # ── 6. Run RBC simulation ────────────────────────────────────
    rbc_controller = RbcController(
        n_actuators=N_ACTUATORS,
        u_min=u_min_W_m2,
        u_max=u_max_W_m2,
        deadband=rbc_deadband,
    )

    print("\n━━━ Running RBC simulation ━━━")
    with timed("RBC simulation"):
        rbc_results_df = run_simulation(
            plant=plant,
            warmup_controller=rbc_controller,
            eval_controller=rbc_controller,
            observer=observer,
            config=simulation_config,
            df=controller_input_df,
        )

    rbc_eval = rbc_results_df[
        rbc_results_df["simulation_phase"] == SimulationPhase.EVALUATION
    ]
    rbc_perf_row = hvac_control_performance_metrics(rbc_eval).iloc[0]

    # ── 7. Run MPC simulation ────────────────────────────────────
    mpc_controller = EconomicMPCController(
        model=sys_learned,
        horizon=mpc_horizon_hours * controller_steps_per_hour,
        R_weights=R_weights,
        slack_weights=slack_weights,
        lambda_du=lambda_du,
        u_min_physical=u_min_W_m2,
        u_max_physical=u_max_W_m2,
        scalers=scalers,
        margins=np.zeros(N_ACTUATORS) if margins is None else margins,
    )

    print("\n━━━ Running MPC simulation ━━━")
    with timed("MPC simulation"):
        mpc_results_df = run_simulation(
            plant=plant,
            warmup_controller=rbc_controller,
            eval_controller=mpc_controller,
            observer=observer,
            config=simulation_config,
            df=controller_input_df,
        )

    mpc_eval = mpc_results_df[
        mpc_results_df["simulation_phase"] == SimulationPhase.EVALUATION
    ]
    mpc_perf_row = hvac_control_performance_metrics(mpc_eval).iloc[0]

    # ── 8. Filter, plot, and report ──────────────────────────────
    results = {
        "RBC": rbc_results_df,
        "MPC": mpc_results_df,
    }
    evaluation_results = {
        "RBC": rbc_eval,
        "MPC": mpc_eval,
    }

    mpc_fig = plot_simulation_results_multiple_controllers(results=evaluation_results)
    mpc_fig.show()

    metric_summary = _build_metric_summary(rbc_perf_row, mpc_perf_row)
    _print_metric_table(metric_summary)

    # ── 8b. Pareto fronts: MPC + RBC, highlight both selected ───
    pareto_fig = plot_pareto_dominant(
        studies=[
            ParetoStudy(
                db_path=p.mpc_db,
                study_name=p.mpc_study,
                label=MPC_STYLE[0],
                colour=MPC_STYLE[1],
            ),
            ParetoStudy(
                db_path=p.rbc_db,
                study_name=p.rbc_study,
                label=RBC_STYLE[0],
                colour=RBC_STYLE[1],
            ),
        ],
        target_names=("Energy (Wh)", "Comfort violation (K·h)"),
        highlight=[
            {
                "x": float(rbc_trial.values[0]),
                "y": float(rbc_trial.values[1]),
                "trial_number": rbc_trial.number,
                "direction": "right",
            },
            {
                "x": float(mpc_trial.values[0]),
                "y": float(mpc_trial.values[1]),
                "trial_number": mpc_trial.number,
                "direction": "left",
            },
        ],
        ylim=(0, 40),
        xlim=(8e5, 1.13e6),
    )

    # ── 9. Save results ──────────────────────────────────────────
    results_dir = Path(paths.output_dir) / "eval_hopt" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    mpc_fig.savefig(results_dir / "simulation_results.pdf")
    print(
        f"\n📄  Simulation results plot saved to {results_dir / 'simulation_results.pdf'}"
    )

    pareto_fig.savefig(results_dir / "mpc_pareto_front.pdf")
    print(f"📄  MPC Pareto front saved to {results_dir / 'mpc_pareto_front.pdf'}")

    tbl_path = _write_latex_table(metric_summary, results_dir / "performance_table.tex")
    print(f"📘  LaTeX table saved to {tbl_path}")

    _save_metrics_json(
        rbc_perf_row,
        mpc_perf_row,
        metric_summary,
        results_dir / "performance_metrics.json",
    )

    pareto_fig.show()

    print("Done")


if __name__ == "__main__":
    main()
