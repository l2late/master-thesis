"""
Model Provisioning abstraction for the MPC hyperparameter optimization pipeline.

Defines a unified `ModelBundle` and a `ModelProvider` protocol that can source
trained models from any location (local filesystem, WandB, etc.) while presenting
a consistent interface to downstream consumers.

Key design decision: ModelBundle.run_dir is a **local directory** that structurally
mirrors a Hydra run directory (contains `checkpoints/last.ckpt` and
`.hydra/config.yaml`).  This means `load_learned_lti_ss()` consumes it without
any modification.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import wandb

from alphabuilding.infrastructure.wandb.utils import (
    WandBPath,
    download_config_artifact_from_wandb,
    download_model_checkpoint_from_wandb,
)
from alphabuilding.utils.paths import paths

REQUIRED_CHECKPOINT = Path("checkpoints") / "last.ckpt"
REQUIRED_CONFIG = Path(".hydra") / "config.yaml"


def is_valid_run_dir(p: Path) -> bool:
    """Check if a directory contains the required Hydra artifacts."""
    return (p / REQUIRED_CHECKPOINT).is_file() and (p / REQUIRED_CONFIG).is_file()


@dataclass(frozen=True)
class ModelBundle:
    """
    Unified model artifact bundle — works for any source (local, WandB, etc.).

    Attributes:
        run_dir: Local directory containing `checkpoints/last.ckpt` and
                 `.hydra/config.yaml`.  This is the path expected by
                 `load_learned_lti_ss()`.
        wandb_run_id: WandB run_id if sourced from WandB, else None.
        wandb_run_name: Human-readable run name if available.
        wandb_metadata: Arbitrary provenance metadata (config, summary, tags, ...).
    """

    run_dir: Path
    wandb_run_id: str | None = None
    wandb_run_name: str | None = None
    wandb_metadata: dict = field(default_factory=dict)


class ModelProvider(Protocol):
    """Contract: anything that can supply a :class:`ModelBundle`."""

    def provide(self) -> ModelBundle:  # pragma: no cover
        ...


@dataclass
class LocalModelProvider:
    """
    For local development — points to an existing Hydra log directory.

    The run_dir must contain:
        - {run_dir}/checkpoints/last.ckpt
        - {run_dir}/.hydra/config.yaml
    """

    run_dir: Path

    def provide(self) -> ModelBundle:
        resolved = self.run_dir.resolve()
        if not is_valid_run_dir(resolved):
            raise FileNotFoundError(
                f"Not a valid run directory: {resolved}\n"
                f"Expected: {REQUIRED_CHECKPOINT} and {REQUIRED_CONFIG}"
            )
        return ModelBundle(
            run_dir=resolved,
            wandb_metadata={"source": "local"},
        )


@dataclass
class WandBModelProvider:
    """
    Downloads model artifacts from WandB to a local cache directory, then
    assembles a :class:`ModelBundle` pointing at that cache.

    The cache directory is structured exactly like a Hydra run directory::

        {cache_dir}/{run_id}/
        ├── checkpoints/
        │   └── last.ckpt
        └── .hydra/
            └── config.yaml

    This structure mirrors a Hydra run dir, so `load_learned_lti_ss()` works
    without modification.

    Example usage::

        provider = WandBModelProvider(
            entity="my-org",
            project="alpha-building",
            run_id="abc123xyz",
            cache_dir=Path("/workspace/wandb_cache"),
        )
        bundle = provider.provide()
        print(bundle.run_dir)  # /workspace/wandb_cache/abc123xyz
    """

    entity: str
    project: str
    run_id: str
    cache_dir: Path | None = None

    def __post_init__(self) -> None:
        if self.cache_dir is None:
            self.cache_dir = Path(paths.artifact_dir) / "wandb_cache"

    def provide(self) -> ModelBundle:
        cache = self.cache_dir / self.run_id
        ckpt_dir = cache / "checkpoints"
        config_dir = cache / ".hydra"
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)

        wandb_path = WandBPath(self.entity, self.project, self.run_id)

        # ── Download model checkpoint ──────────────────────────────────
        src_ckpt = download_model_checkpoint_from_wandb(
            wandb_path, download_dir=ckpt_dir
        )
        dst_ckpt = ckpt_dir / "last.ckpt"
        if not dst_ckpt.exists():
            shutil.copy2(src_ckpt, dst_ckpt)

        # ── Download config file ───────────────────────────────────────
        src_cfg = download_config_artifact_from_wandb(
            wandb_path, download_dir=config_dir
        )
        dst_cfg = config_dir / "config.yaml"
        if not dst_cfg.exists():
            shutil.copy2(src_cfg, dst_cfg)

        # ── Fetch run metadata for provenance tracking ─────────────────
        api = wandb.Api()
        run = api.run(wandb_path.run_path)
        metadata: dict = {
            "source": "wandb",
            "run_name": run.name,
            "tags": run.tags,
        }

        return ModelBundle(
            run_dir=cache.resolve(),
            wandb_run_id=self.run_id,
            wandb_run_name=run.name,
            wandb_metadata=metadata,
        )
