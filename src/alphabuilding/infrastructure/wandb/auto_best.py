"""
Auto-best WandB run resolution.

Wraps :func:`get_best_run_id_from_wandb` with sensible defaults so the MPC
HPO pipeline can use ``--auto-best`` without hard-coding filters in the CLI.
"""

from __future__ import annotations

from typing import Any

from alphabuilding.infrastructure.wandb.utils import (
    WandBPath,
    get_best_run_id_from_wandb,
)

# ── Defaults ───────────────────────────────────────────────────────────
# Mirrors the filters used in scripts/WIP/get_best_run_id_from_wandb.py
DEFAULT_RUN_FILTERS: dict[str, Any] = {
    "state": "finished",
    "config.model.topology": {"$eq": "PHYSICAL_ONE_TO_ONE"},
    "config.model.lambda_eigenvals_stability_penalty": {"$eq": 1.0},
}

DEFAULT_METRIC_KEY = "val/rmse_celsius"


def resolve_best_wandb_run(
    entity: str,
    project: str,
    metric_key: str = DEFAULT_METRIC_KEY,
    run_filters: dict[str, Any] | None = None,
    minimize: bool = True,
) -> WandBPath:
    """
    Resolve the best WandB run_id from filters, returning a :class:`WandBPath`.

    Args:
        entity: WandB entity name.
        project: WandB project name.
        metric_key: Metric to optimise (lower is better if minimize=True).
        run_filters: MongoDB-style filters dict; defaults to
            :const:`DEFAULT_RUN_FILTERS`.
        minimize: ``True`` for min (e.g., RMSE), ``False`` for max.

    Returns:
        :class:`WandBPath` with run_id populated.
    """
    if run_filters is None:
        run_filters = DEFAULT_RUN_FILTERS

    wandb_path = WandBPath(entity=entity, project=project)
    run_id = get_best_run_id_from_wandb(
        wandb_path, metric_key, run_filters, minimize=minimize
    )
    return WandBPath(entity=entity, project=project, run_id=run_id)
