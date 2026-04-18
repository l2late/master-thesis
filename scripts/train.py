import logging
from pathlib import Path

import hydra
import lightning as L
import numpy as np
import torch
from hydra.core.hydra_config import HydraConfig
from hydra.utils import instantiate
from lightning.pytorch.loggers import WandbLogger
from omegaconf import DictConfig, OmegaConf

import alphabuilding.config_schemas
import alphabuilding.utils.paths
from alphabuilding.analysis.plot_system_matrices import plot_A_and_B_matrices

# from alphabuilding.infrastructure.lightning.callbacks.hyperparameter_scheduling
# import (
#     CosineAnnealingHparam,
#     ExponentialHparam,
# )
from alphabuilding.utils.chooser import choose_run_dir

# this is needed even if we don't use it directly in this file because paths are set in that module
# from alphabuilding.utils.paths import PathsConfig, paths
from alphabuilding.utils.utils import instantiate_callbacks

python_logger = logging.getLogger(__name__)
torch.set_default_dtype(torch.float64)


def setup_wandb_logger(
    cfg: DictConfig, model: L.LightningModule
) -> L.pytorch.loggers.Logger | None:
    if not cfg.get("logger"):
        return None

    # Instantiate directly; YAML interpolation handles group, tags, and name
    logger = instantiate(cfg.logger)

    if isinstance(logger, WandbLogger):
        logger.experiment.config.update(
            OmegaConf.to_container(cfg, resolve=True, throw_on_missing=False)
        )
        logger.watch(model, log="all", log_freq=100, log_graph=False)

    return logger


def log_wandb_artifacts(logger: WandbLogger):
    """Logs Hydra configs and overrides as W&B artifacts."""
    import wandb

    hydra_output_dir = Path(HydraConfig.get().runtime.output_dir)

    config_artifact = wandb.Artifact(
        name=f"config-{logger.experiment.id}",
        type="config",
    )
    config_artifact.add_file(
        str(hydra_output_dir / ".hydra" / "config.yaml"), name="config.yaml"
    )
    config_artifact.add_file(
        str(hydra_output_dir / ".hydra" / "overrides.yaml"), name="overrides.yaml"
    )

    logger.experiment.log_artifact(config_artifact)


def check_and_visualize_matrices(cfg: DictConfig, model: L.LightningModule):
    """Checks for unstable eigenvalues and visualizes system matrices if requested."""
    A_matrix = model.dynamics.A_matrix.detach().cpu().numpy()
    eigenvalues = np.linalg.eigvals(A_matrix)
    unstable_eigenvalues = [ev for ev in eigenvalues if np.real(ev) > 0]

    if len(unstable_eigenvalues) > 0:
        python_logger.warning(
            f"UNSTABLE EIGENVALUES detected in A matrix: {unstable_eigenvalues}"
        )

    if cfg.get("visualize_init_matrices", False):
        python_logger.info("Visualizing initial A and B matrices...")
        B_matrix = model.dynamics.B_matrix.detach().cpu().numpy()
        plot_A_and_B_matrices(A_matrix, B_matrix)


@hydra.main(version_base="1.3", config_path="../conf", config_name="train")
def train(cfg: DictConfig) -> float:
    # --- 1. Setup & Seeding ---
    if cfg.get("seed"):
        L.seed_everything(cfg.seed, workers=True)

    python_logger.info("\n" + OmegaConf.to_yaml(cfg))

    # Disable num_workers because all data fits on GPU
    cfg.datamodule.num_workers = 0

    # --- 2. Resume Logic ---
    if cfg.get("resume_training"):
        python_logger.info(f"Resuming training for model <{cfg.model._target_}>")
        dir_path = choose_run_dir(cfg.paths.log_dir)
        checkpoint = dir_path / "checkpoints" / "last.ckpt"

        if not checkpoint.exists():
            raise FileNotFoundError(f"Missing checkpoint: {checkpoint}")
        cfg.ckpt_path = str(checkpoint)

    # --- 3. Instantiation ---
    model: L.LightningModule = instantiate(cfg.model)
    datamodule: L.LightningDataModule = instantiate(cfg.datamodule)
    callbacks: list[L.Callback] = instantiate_callbacks(cfg.get("callbacks"))

    check_and_visualize_matrices(cfg, model)
    logger = setup_wandb_logger(cfg, model)

    # --- 4. Training ---
    trainer: L.Trainer = instantiate(cfg.trainer, callbacks=callbacks, logger=logger)

    if cfg.get("train"):
        python_logger.info("Starting training!")
        trainer.fit(model=model, datamodule=datamodule, ckpt_path=cfg.get("ckpt_path"))

    # --- 5. Post-Training W&B Logging ---
    if isinstance(logger, WandbLogger):
        log_wandb_artifacts(logger)
        # TODO: Call evaluation plotting functions here, save them to HydraConfig.get().runtime.output_dir
        # and log them to W&B via `logger.experiment.log({"eval/plot_name": wandb.Image(plot_path)})`

    # --- 6. Testing ---
    if cfg.get("test"):
        python_logger.info("Starting testing!")
        trainer.test(model=model, datamodule=datamodule)

    return float(trainer.callback_metrics.get("val/rmse_celcius", float("inf")))


if __name__ == "__main__":
    train()
