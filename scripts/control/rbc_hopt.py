#!/usr/bin/env python
"""
RBC Hyperparameter Optimisation — CLI Entry Point

Runs Optuna multi-objective optimisation over RBC hyperparameters
(economic energy ↔ comfort violation Pareto front).

Unlike MPC, RBC does NOT require a trained model — the controller logic is
purely rule-based (hysteresis / dead-band).  The only reason a model is
loaded is to satisfy the simulation harness, which needs a Luenberger
observer and a data-module for test disturbances and scalers.  Any
compatible checkpoint will serve this purpose.

Optimised hyperparameters
-------------------------
- ``u_max``    : Maximum heating power per actuator in W/m² (shared across zones)
- ``deadband`` : Hysteresis deadband in °C (shared across zones)

Usage examples
--------------
Local Hydra run directory -- model only needed for the simulation harness::

    python scripts/control/rbc_hopt.py \\\\
        --run-dir logs/train/runs/2026-03-24_17-37-19 \\\\
        --n-trials 5000

WandB specific run::

    python scripts/control/rbc_hopt.py \\\\
        --entity my-org --project alpha-building \\\\
        --run-id abc123xyz --n-trials 500

WandB auto-best (pick best finished run)::

    python scripts/control/rbc_hopt.py \\\\
        --entity my-org --project alpha-building \\\\
        --auto-best --n-trials 500

Monitor live::

    optuna dashboard \\\\
        --storage journal:///workspace/output/rbc_hopt/optuna_rbc.journal \\\\
        --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

import optuna
from joblib import Parallel, delayed

from alphabuilding.infrastructure.wandb.auto_best import resolve_best_wandb_run

from alphabuilding.control.model_provision import LocalModelProvider, WandBModelProvider
from alphabuilding.control.storage_strategy import (
    StorageConfig,
    StorageType,
    create_storage,
)
from alphabuilding.control.sweep_mpc_simulations import (
    optimize_rbc_optuna_study_worker,
)
from alphabuilding.control.types import SimulationConfig
from alphabuilding.utils.paths import paths

# ── Default WandB filters for --auto-best ──────────────────────────
# Must mirror the MPC hopt filters so that `--auto-best` returns the same
# run ID.  This guarantees RBC and EMPC are evaluated on the same dataset
# (datamodule scalers, test disturbances, comfort bounds, noise levels, …).
DEFAULT_RUN_FILTERS = {
    "state": "finished",
    "summary_metrics.epoch": {"$eq": 499},
    "config.model.topology": {"$eq": "PHYSICAL_ONE_TO_ONE"},
    "config.model.lambda_eigenvals_stability_penalty": {"$eq": 1.0},
}

# ── Default WandB coordinates ─────────────────────────────────────
# Mirrors conf/logger/wandb.yaml so that `--auto-best` works out-of-the-box
# and both MPC and RBC hopt default to the same project.
DEFAULT_WANDB_ENTITY = os.environ.get("WANDB_ENTITY", "l2late")
DEFAULT_WANDB_PROJECT = os.environ.get("WANDB_PROJECT", "BuildingThermalDynamics")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="RBC Hyperparameter Optimisation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # ── Model Source ───────────────────────────────────────────────
    # Model is ONLY needed for the simulation harness (observer + scalers).
    # The RBC controller itself is model-free.
    src = p.add_argument_group("Model source (simulation harness only)")
    src.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Path to local Hydra run directory containing checkpoints/.hydra",
    )
    src.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Specific WandB run_id",
    )
    src.add_argument(
        "--auto-best",
        action="store_true",
        default=True,
        help="Auto-select the best finished run (uses --entity / --project) — default: enabled",
    )
    src.add_argument(
        "--no-auto-best",
        action="store_false",
        dest="auto_best",
        help="Disable auto-best run selection",
    )
    src.add_argument(
        "--entity",
        default=DEFAULT_WANDB_ENTITY,
        help="WandB entity  (default: %(default)s; env: WANDB_ENTITY)",
    )
    src.add_argument(
        "--project",
        default=DEFAULT_WANDB_PROJECT,
        help="WandB project (default: %(default)s; env: WANDB_PROJECT)",
    )
    src.add_argument(
        "--download-dir",
        type=Path,
        help="Local directory to cache WandB artifact downloads",
    )

    # ── Optuna Config ──────────────────────────────────────────────
    opt = p.add_argument_group("Optuna")
    opt.add_argument(
        "--n-trials",
        type=int,
        default=5000,
        help="Total number of optimisation trials (default: %(default)s)",
    )
    opt.add_argument(
        "--n-startup",
        type=int,
        default=200,
        help="Random startup trials before TPE kicks in (default: %(default)s)",
    )
    opt.add_argument(
        "--storage",
        choices=["sqlite", "journal", "mysql"],
        default="sqlite",
        help="Optuna storage backend (default: %(default)s; journal is safest for remote)",
    )
    opt.add_argument(
        "--study-name",
        type=str,
        help="Study name  (default: auto-generated from model dir)",
        default=None,
    )

    # ── Simulation Config ──────────────────────────────────────────
    sim = p.add_argument_group("Simulation")
    sim.add_argument(
        "--warmup-days",
        type=int,
        default=14,
        help="RBC warm-up period in days (default: %(default)s)",
    )
    sim.add_argument(
        "--eval-days",
        type=int,
        default=7,
        help="Evaluation period in days (default: %(default)s)",
    )
    sim.add_argument(
        "--controller-timestep-min",
        type=int,
        default=15,
        help="Controller timestep in minutes (default: %(default)s)",
    )
    sim.add_argument(
        "--plant-timestep-sec",
        type=int,
        default=30,
        help="Plant simulator timestep in seconds (default: %(default)s)",
    )

    # ── Output ─────────────────────────────────────────────────────
    out = p.add_argument_group("Output")
    out.add_argument(
        "--output-dir",
        type=Path,
        default=Path(paths.output_dir) / "rbc_hopt",
        help="Root output directory (default: %(default)s)",
    )

    # ── Parallelism ────────────────────────────────────────────────
    par = p.add_argument_group("Parallelism")
    par.add_argument(
        "--n-jobs",
        type=int,
        default=None,
        help="Number of parallel workers  (default: CPU count − 2)",
    )
    par.add_argument(
        "--leave-cpus",
        type=int,
        default=2,
        help="CPUs to leave free when auto-detecting n-jobs (default: %(default)s)",
    )

    return p


def _resolve_model_provider(args: argparse.Namespace):
    """Select and configure the appropriate ModelProvider.

    RBC itself does not need a model -- this is only loaded to satisfy the
    simulation harness (Luenberger observer + datamodule scalers / input data).
    Any compatible model will serve this purpose.
    """
    if args.run_dir is not None:
        return LocalModelProvider(run_dir=args.run_dir)

    # WandB path
    # Explicit --run-id overrides default --auto-best
    if args.run_id is not None:
        run_id = args.run_id
    elif args.auto_best:
        if not args.entity or not args.project:
            raise SystemExit(
                "Error: --auto-best requires --entity and --project "
                "(or set WANDB_ENTITY / WANDB_PROJECT env vars)"
            )
        wandb_path = resolve_best_wandb_run(
            entity=args.entity,
            project=args.project,
            run_filters=DEFAULT_RUN_FILTERS,
        )
        run_id = wandb_path.run_id
    else:
        raise SystemExit(
            "Error: specify --run-dir, --run-id, or use --auto-best (default)"
        )

    return WandBModelProvider(
        entity=args.entity,
        project=args.project,
        run_id=run_id,
        cache_dir=args.download_dir,
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # ════════════════════════════════════════════
    #  1. Resolve model source (harness only)
    # ════════════════════════════════════════════
    provider = _resolve_model_provider(args)
    model_bundle = provider.provide()

    print(f"Model source : {model_bundle.wandb_metadata.get('source', 'local')}")
    if model_bundle.wandb_run_id:
        print(
            f"WandB run    : {model_bundle.wandb_run_id}  ({model_bundle.wandb_run_name})"
        )
    print(f"Model bundle : {model_bundle.run_dir}")

    # ════════════════════════════════════════════
    #  2. Create timestamped output directory
    # ════════════════════════════════════════════
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_dir / ts
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output dir   : {output_dir}")

    # ════════════════════════════════════════════
    #  3. Create Optuna study
    # ════════════════════════════════════════════
    study_name = args.study_name or f"rbc_tuning_{model_bundle.run_dir.name}"

    storage_ext_map = {"sqlite": "db", "journal": "log", "mysql": "db"}
    storage_path = output_dir / f"optuna_rbc.{storage_ext_map[args.storage]}"

    storage_config = StorageConfig(
        storage_type=StorageType(args.storage),
        path=storage_path,
    )
    storage = create_storage(storage_config)

    sampler = optuna.samplers.TPESampler(
        n_startup_trials=args.n_startup,
        multivariate=True,
    )

    _ = optuna.create_study(
        study_name=study_name,
        sampler=sampler,
        storage=storage,
        directions=["minimize", "minimize"],
        load_if_exists=True,
    )
    print(f"Study name   : {study_name}")
    print(f"Storage      : {args.storage} → {storage_path}")

    # ════════════════════════════════════════════
    #  4. Build simulation config
    # ════════════════════════════════════════════
    ctrl_sec = args.controller_timestep_min * 60
    ratio = ctrl_sec // args.plant_timestep_sec
    warmup_steps = args.warmup_days * 24 * 4 * ratio
    eval_steps = args.eval_days * 24 * 4 * ratio

    simulation_config = SimulationConfig(
        warmup_steps=warmup_steps,
        eval_steps=eval_steps,
    )

    # ════════════════════════════════════════════
    #  5. Run parallel optimisation
    # ════════════════════════════════════════════
    cpu_count = os.cpu_count() or 1
    n_jobs = args.n_jobs or max(1, cpu_count - args.leave_cpus)

    trials_per_worker = [args.n_trials // n_jobs] * n_jobs
    for i in range(args.n_trials % n_jobs):
        trials_per_worker[i] += 1

    print(f"Parallelising {args.n_trials} trials across {n_jobs} workers…")

    Parallel(n_jobs=n_jobs, verbose=10)(
        delayed(optimize_rbc_optuna_study_worker)(
            study_name=study_name,
            storage_config=storage_config,
            n_trials=n_worker_trials,
            model_bundle=model_bundle,
            simulation_config=simulation_config,
            output_dir=output_dir,
        )
        for n_worker_trials in trials_per_worker
        if n_worker_trials > 0
    )

    print("\nOptuna optimisation completed.")
    print(f"Results stored in: {output_dir}")


if __name__ == "__main__":
    main()
