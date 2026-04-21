#!/usr/bin/env python
"""
MPC Hyperparameter Optimisation — CLI Entry Point

Sources a trained model from either a local Hydra run directory or WandB,
then runs Optuna multi-objective optimisation over MPC hyperparameters
(economic energy ↔ comfort violation Pareto front).

Usage examples
--------------
WandB best-run (auto-select)::

    python scripts/control/mpc_hopt.py \\
        --source wandb --auto-best --n-trials 5000

WandB specific run::

    python scripts/control/mpc_hopt.py \\
        --source wandb --run-id abc123xyz --n-trials 3000

Local Hydra run directory::

    python scripts/control/mpc_hopt.py \\
        --source local \\
        --run-dir logs/train/runs/2026-03-24_17-37-19 \\
        --n-trials 500

Monitor live on Vast.ai (port-forward via SSH)::

    optuna dashboard \\
        --storage journal:///workspace/output/mpc_hopt/optuna_mpc.journal \\
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
    optimize_optuna_study_worker,
)
from alphabuilding.control.types import SimulationConfig
from alphabuilding.utils.paths import paths

# ── Default WandB filters ──────────────────────────────────────────────
# Mirrors scripts/WIP/get_best_run_id_from_wandb.py
DEFAULT_RUN_FILTERS = {
    "state": "finished",
    "summary_metrics.epoch": {"$eq": 499},
    "config.model.topology": {"$eq": "PHYSICAL_ONE_TO_ONE"},
    "config.model.lambda_eigenvals_stability_penalty": {"$eq": 1.0},
}

DEFAULT_METRIC_KEY = "val/rmse_celsius"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MPC Hyperparameter Optimisation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # ── Model Source ───────────────────────────────────────────────
    src = p.add_argument_group("Model source")
    src.add_argument(
        "--source",
        choices=["local", "wandb"],
        default="wandb",
        help="Where to load the model from (default: wandb)",
    )
    src.add_argument(
        "--run-dir",
        type=Path,
        help="Path to local Hydra run directory (required for --source local)",
    )
    src.add_argument(
        "--entity",
        default=os.environ.get("WANDB_ENTITY"),
        help="WandB entity  (env: WANDB_ENTITY)",
    )
    src.add_argument(
        "--project",
        default=os.environ.get("WANDB_PROJECT"),
        help="WandB project (env: WANDB_PROJECT)",
    )
    src.add_argument("--run-id", help="Specific WandB run_id")
    src.add_argument(
        "--auto-best",
        action="store_true",
        help="Auto-select the best run via metric + filters",
    )
    src.add_argument(
        "--metric-key",
        default=DEFAULT_METRIC_KEY,
        help="Metric for --auto-best selection (default: %(default)s)",
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
        help="MPC evaluation period in days (default: %(default)s)",
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
        default=Path(paths.output_dir) / "mpc_hopt",
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
    """Select and configure the appropriate ModelProvider."""

    if args.source == "local":
        if args.run_dir is None:
            raise SystemExit("Error: --source local requires --run-dir")
        provider = LocalModelProvider(run_dir=args.run_dir)

    elif args.source == "wandb":
        if not args.entity or not args.project:
            raise SystemExit(
                "Error: --source wandb requires --entity and --project "
                "(or set WANDB_ENTITY / WANDB_PROJECT env vars)"
            )

        # Determine run_id
        if args.auto_best:
            wandb_path = resolve_best_wandb_run(
                entity=args.entity,
                project=args.project,
                metric_key=args.metric_key,
                run_filters=DEFAULT_RUN_FILTERS,
            )
            run_id = wandb_path.run_id
        elif args.run_id:
            run_id = args.run_id
        else:
            raise SystemExit("Error: --source wandb requires --auto-best or --run-id")

        provider = WandBModelProvider(
            entity=args.entity,
            project=args.project,
            run_id=run_id,
            cache_dir=args.download_dir,
        )

    else:  # pragma: no cover — argparse guards this
        raise ValueError(f"Unknown source: {args.source}")

    return provider


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # ════════════════════════════════════════════
    #  1. Resolve model source
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
    study_name = args.study_name or f"mpc_tuning_{model_bundle.run_dir.name}"

    storage_ext_map = {"sqlite": "db", "journal": "log", "mysql": "db"}
    storage_path = output_dir / f"optuna_mpc.{storage_ext_map[args.storage]}"

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
        delayed(optimize_optuna_study_worker)(
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
