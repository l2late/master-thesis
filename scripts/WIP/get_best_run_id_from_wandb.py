import os

from alphabuilding.infrastructure.wandb.utils import (
    WandBPath,
    download_config_artifact_from_wandb,
    download_model_checkpoint_from_wandb,
    get_best_run_id_from_wandb,
)

wandb_path = WandBPath(
    entity=os.environ["WANDB_ENTITY"], project=os.environ["WANDB_PROJECT"]
)

group_key = "experiment_name"  # None
metric_key = "val/rmse_celsius"  # None

# %%

run_filters = {
    "state": "finished",
    "summary_metrics.epoch": {"$eq": 499},
    "config.model.topology": {
        # "$in": ["FULLY_CONNECTED_ONE_TO_ONE", "PHYSICAL_ONE_TO_ONE"]
        "$eq": "PHYSICAL_ONE_TO_ONE"
    },
    "config.model.lambda_eigenvals_stability_penalty": {
        "$eq": 1.0,
    },
}


# %%

run_id = get_best_run_id_from_wandb(wandb_path, metric_key, run_filters)
wandb_path.run_id = run_id


def instantiate_model_from_wandb(wandb_path: WandBPath):
    config_path = download_config_artifact_from_wandb(wandb_path)
    model_ckpt_path = download_model_checkpoint_from_wandb(wandb_path)
    # instantiate module from config and checkpoint
    # instantiate datamodule from config
    return model
