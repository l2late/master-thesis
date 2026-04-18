import logging
import tempfile
from pathlib import Path

import lightning as L
import optuna
from hydra import compose, initialize_config_dir
from hydra.utils import instantiate
from lightning.pytorch.loggers import WandbLogger
from omegaconf import OmegaConf
from optuna_integration import PyTorchLightningPruningCallback

from alphabuilding.utils.paths import PathsConfig, paths
from alphabuilding.utils.utils import instantiate_callbacks

log = logging.getLogger(__name__)
CONF_DIR = str(Path(__file__).parent.parent / "conf")


def objective(trial: optuna.Trial) -> float:
    overrides = [
        "experiment=hpo_baseline",
        f"model.lr={trial.suggest_float('lr', 1e-3, 5e-2, log=True)}",
        f"model.lambda_observer={trial.suggest_float('lambda_observer', 0.0, 5.0)}",
        f"model.lambda_eigenvals_stability_penalty={trial.suggest_float('lambda_eigenvals_stability_penalty', 0, 1)}",
        # f"model.num_latent_states={trial.suggest_int('num_latent_states', 0, 10)}",
        f"paths.output_dir={Path.cwd() / 'output'}",
        f"paths.work_dir={Path.cwd()}",
        # "callbacks=hpo",
    ]

    with initialize_config_dir(config_dir=CONF_DIR, version_base="1.3"):
        cfg = compose(config_name="train", overrides=overrides)

    L.seed_everything(cfg.seed, workers=True)
    model: L.LightningModule = instantiate(cfg.model)
    datamodule: L.LightningDataModule = instantiate(cfg.datamodule)

    callbacks: list[L.Callback] = instantiate_callbacks(cfg.get("callbacks"))
    pruning_cb = PyTorchLightningPruningCallback(trial, monitor="val/rmse_celsius")
    callbacks.append(pruning_cb)

    logger = instantiate(cfg.logger) if cfg.get("logger") else None

    trainer: L.Trainer = instantiate(
        cfg.trainer,
        callbacks=callbacks,
        logger=logger,
        enable_checkpointing=True,
        enable_progress_bar=False,
    )

    # log the config to Wandb as well, so that it's visible in the UI and can be compared across runs.
    # We log both the full config and the overrides, so that we can easily see what was changed for this run compared to the default config.
    if isinstance(logger, WandbLogger):
        logger.experiment.config.update(
            OmegaConf.to_container(cfg, resolve=True, throw_on_missing=False)
        )
        logger.experiment.config.update(
            {
                "trial_number": trial.number,
            }
        )

    try:
        trainer.fit(model=model, datamodule=datamodule)

        if isinstance(logger, WandbLogger):
            import wandb

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                # config.yaml — identical to what @hydra.main writes
                OmegaConf.save(cfg, tmp_path / "config.yaml")

                # overrides.yaml — Hydra writes this as a plain YAML list
                OmegaConf.save(OmegaConf.create(overrides), tmp_path / "overrides.yaml")

                config_artifact = wandb.Artifact(
                    name=f"config-{logger.experiment.id}",
                    type="config",
                )
                config_artifact.add_file(
                    str(tmp_path / "config.yaml"), name="config.yaml"
                )
                config_artifact.add_file(
                    str(tmp_path / "overrides.yaml"), name="overrides.yaml"
                )
                logger.experiment.log_artifact(config_artifact)
    finally:
        if isinstance(logger, WandbLogger):
            logger.experiment.finish()  # Ensure the run is marked as finished in Wandb

    return float(trainer.callback_metrics.get("val/rmse_celsius", float("inf")))


if __name__ == "__main__":
    import torch
    from optuna.storages import RDBStorage

    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(0.25, device=0)
        torch.cuda.empty_cache()

    N_TRIALS = 500
    N_STARTUP_TRIALS = 15

    # No fixed seed for the sampler so different workers explore different parts of the search space.
    sampler = optuna.samplers.GPSampler(n_startup_trials=N_STARTUP_TRIALS)

    pruner = optuna.pruners.HyperbandPruner(
        min_resource=100,  # Equivalent to n_warmup_steps (earliest epoch it can prune)
        reduction_factor=3,  # How aggressively it prunes (3 is standard/default)
    )

    # 2. ENSURE DB DIRECTORY EXISTS
    db_path = Path("logs/optuna/optuna_studies.db").resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    STORAGE_URL = f"sqlite:///{db_path}"

    # 3. ADD SQLITE TIMEOUT TO PREVENT "DATABASE IS LOCKED" CRASHES
    storage_backend = RDBStorage(
        url=STORAGE_URL,
        engine_kwargs={"connect_args": {"timeout": 60.0}},
    )

    study = optuna.create_study(
        study_name="building_dynamics_hopt",
        direction="minimize",
        storage=storage_backend,
        load_if_exists=True,
        sampler=sampler,
        pruner=pruner,
    )
    if len(study.trials) == 0:
        study.enqueue_trial(
            {
                "lambda_observer": 0.3,
                "lambda_eigenvals_stability_penalty": 0.2,
                "lr": 1e-2,
            }
        )

    # Do NOT pass n_jobs=15 here! (See explanation below)
    study.optimize(objective, n_trials=N_TRIALS)
