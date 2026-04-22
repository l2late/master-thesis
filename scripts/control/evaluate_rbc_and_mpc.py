"""
Evaluate and compare RBC and MPC controllers, extracting best hopt params
from paired Optuna databases (mpc_tuning_<id> ↔ rbc_tuning_<id>).

Usage
-----
    # Point at a directory containing extracted cloud hopt output:
    uv run python scripts/control/evaluate_rbc_and_mpc.py --hopt-dir output/eval_hopt/

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
import pandas as pd
import torch
from optuna.trial import FrozenTrial

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
NP_ROOM_AREAS = np.array(global_config.ROOM_AREAS)

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
) -> "RankedTrial":
    """Convenience: fetch the #1 ranked trial from a study."""
    ranked = get_sorted_best_trials(
        study_name=study_name,
        db_path=db_path,
        strategy=strategy,
        weights=weights,
    )
    assert ranked, f"No best trials found in study '{study_name}'"
    return ranked[0]


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

    # ── 3. Extract best hopt params ──────────────────────────────
    # rbc_trial = _sorted_best_trial(p.rbc_db, p.rbc_study, weights=[4, 5])
    # u_max_W_m2, deadband = rbc_params_from_trial(rbc_trial, n_actuators=N_ACTUATORS)
    # Override to sensible value (1 degC) because RBC tuning leads to very small deadbands
    rbc_deadband = np.ones(5) * 0.5

    mpc_trial = _sorted_best_trial(
        p.mpc_db,
        p.mpc_study,
        weights=[5, 20],  # [Energy, Comfort]
    )  # it works best to put more weight on comfort (10) than energy (9) to get a good controller.
    R_weights, slack_weights, margins = controller_params_from_trial(mpc_trial)
    lambda_du = mpc_trial.params.get("lambda_du", 0.0)
    lambda_du = 1000

    # print(f"\n📊  RBC best trial (rank={rbc_trial.rank}, score={rbc_trial.score:.4f})")
    # print(f"   u_max     = {u_max_W_m2[0]:.4f} W/m²")
    # print(f"   deadband  = {deadband[0]:.4f} °C")
    # print("   (Note: deadband overridden to 1.0 °C for more realistic RBC behavior)")
    print(f"\n📊  MPC best trial (rank={mpc_trial.rank}, score={mpc_trial.score:.4f})")
    print(f"   R_weight     = {R_weights[0]:.4f}")
    print(f"   slack_weight = {slack_weights[0]:.4f}")
    print(f"   lambda_du    = {lambda_du:.4f}")
    print(f"   margins      = {margins}")

    # ── 4. Load model, plant, observer ───────────────────────────
    # Now that we know the model path, pass it directly — no interactive prompt.
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
    max_rad_power_W_m2 = 35.0
    u_min_W_m2 = np.zeros(N_ACTUATORS)
    u_max_W_m2 = np.ones(N_ACTUATORS) * max_rad_power_W_m2

    # Timing
    plant_step_length_seconds = 30
    controller_step_length_seconds = 15 * 60
    controller_steps_per_hour = int(3600 // controller_step_length_seconds)
    assert controller_steps_per_hour == 4
    controller_steps_per_plant_step = (
        controller_step_length_seconds / plant_step_length_seconds
    )

    warm_up_days = 19
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

    # ── 5. Run RBC simulation ────────────────────────────────────
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

    # ── 6. Run MPC simulation ────────────────────────────────────
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

    # ── 7. Filter, plot, and report ──────────────────────────────
    results = {
        "RBC": rbc_results_df,
        "MPC": mpc_results_df,
    }
    evaluation_results = {
        name: df[df["simulation_phase"] == SimulationPhase.EVALUATION]
        for name, df in results.items()
    }

    mpc_fig = plot_simulation_results_multiple_controllers(results=evaluation_results)
    mpc_fig.show()

    # ── 7b. Performance metrics & comparison ────────────────────
    rbc_perf_row = hvac_control_performance_metrics(evaluation_results["RBC"]).iloc[0]
    mpc_perf_row = hvac_control_performance_metrics(evaluation_results["MPC"]).iloc[0]

    metric_summary = _build_metric_summary(rbc_perf_row, mpc_perf_row)
    _print_metric_table(metric_summary)

    # ── 7c. Pareto fronts: MPC + RBC ─────────────────────────────
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
        highlight={
            "x": mpc_trial.trial.values[0],
            "y": mpc_trial.trial.values[1],
            "trial_number": mpc_trial.trial.number,
            "rank": mpc_trial.rank,
        },
        ylim=(0, 50),
        xlim=(8e5, 3.5e6),
    )

    # ── 8. Save results ──────────────────────────────────────────
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
