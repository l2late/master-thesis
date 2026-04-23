"""
Evaluation of the best WandB model.

Uses the auto-best WandB resolution logic to fetch the best model based on
val/rmse_celsius and then runs the full evaluation pipeline (poles,
predictability, system analysis, etc.).

Usage:
    # Auto-select best model from WandB
    uv run python scripts/eval.py

    # Evaluate a specific run
    uv run python scripts/eval.py --run-id abc123xyz

    # Override the metric or filters
    uv run python scripts/eval.py --metric-key val/mae_celsius
"""

import argparse
import os
from pathlib import Path
from typing import Any

import wandb

from alphabuilding.analysis.evaluation import evaluate_model_predictions
from alphabuilding.infrastructure.wandb.auto_best import (
    DEFAULT_METRIC_KEY,
    DEFAULT_RUN_FILTERS,
    resolve_best_wandb_run,
)
from alphabuilding.infrastructure.wandb.utils import (
    WandBPath,
    download_config_artifact_from_wandb,
    download_model_checkpoint_from_wandb,
)
from alphabuilding.utils.paths import paths


def get_wandb_credentials() -> tuple[str, str]:
    """Fetch WandB entity and project from environment variables."""
    entity = os.environ.get("WANDB_ENTITY")
    project = os.environ.get("WANDB_PROJECT")

    if not entity or not project:
        raise RuntimeError(
            "WANDB_ENTITY and WANDB_PROJECT environment variables must be set"
        )

    return entity, project


def resolve_run_path(
    run_id: str | None = None,
    metric_key: str = DEFAULT_METRIC_KEY,
    run_filters: dict[str, Any] | None = None,
) -> WandBPath:
    """
    Resolve a WandB run path.

    If run_id is provided, use it directly.
    Otherwise, auto-select the best run based on the given metric and filters.
    """
    entity, project = get_wandb_credentials()

    if run_id is not None:
        print(f"Using specific run_id: {run_id}")
        return WandBPath(entity=entity, project=project, run_id=run_id)

    print(f"Auto-selecting best run by {metric_key} (minimize=True)...")
    if run_filters:
        print(f"Filters: {run_filters}")

    return resolve_best_wandb_run(
        entity=entity,
        project=project,
        metric_key=metric_key,
        run_filters=run_filters,
    )


def download_model_artifacts(wandb_path: WandBPath) -> tuple[Path, Path]:
    """Download checkpoint and config from WandB, return local paths."""
    cache_root = Path(paths.artifact_dir) / "eval_cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    ckpt_path = download_model_checkpoint_from_wandb(
        wandb_path, download_dir=cache_root
    )
    config_path = download_config_artifact_from_wandb(
        wandb_path, download_dir=cache_root
    )

    return ckpt_path, config_path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Evaluate the best (or a specific) WandB model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--run-id",
        help="WandB run_id to evaluate (default: auto-select best run)",
    )
    p.add_argument(
        "--metric-key",
        default=DEFAULT_METRIC_KEY,
        help="Metric for auto-best selection (default: %(default)s)",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Resolve run
    wandb_path = resolve_run_path(
        run_id=args.run_id,
        metric_key=args.metric_key,
    )
    print(f"WandB path   : {wandb_path.run_path}")

    # Download artifacts
    ckpt_path, config_path = download_model_artifacts(wandb_path)
    print(f"Checkpoint   : {ckpt_path}")
    print(f"Config       : {config_path}")

    # Run evaluation
    evaluate_model_predictions(ckpt_path, config_path)
    print("Done")


if __name__ == "__main__":
    main()
