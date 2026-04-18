import os
import time
from functools import wraps
from importlib.util import find_spec
from pathlib import Path
from typing import Callable

import hydra
import yaml
from lightning import Callback
from lightning.pytorch.loggers import Logger
from lightning.pytorch.utilities import model_summary, rank_zero_only
from omegaconf import DictConfig

from alphabuilding.utils import pylogger

log = pylogger.get_pylogger(__name__)


def instantiate_callbacks(callbacks_cfg: DictConfig) -> list[Callback]:
    """Instantiates callbacks from config."""
    callbacks: list[Callback] = []

    if not callbacks_cfg:
        log.warning("Callbacks config is empty.")
        return callbacks

    for cb_key, cb_conf in callbacks_cfg.items():
        if isinstance(cb_conf, DictConfig) and "_target_" in cb_conf:
            log.info(f"Instantiating callback <{cb_conf._target_}>")
            callbacks.append(hydra.utils.instantiate(cb_conf))

    return callbacks


# @rank_zero_only
# def instantiate_loggers(logger_cfg: DictConfig) -> list[Logger]:
#     """Instantiates loggers from config."""
#     logger: list[Logger] = []
#
#     if not logger_cfg:
#         log.warning("Logger config is empty.")
#         return logger
#
#     if not isinstance(logger_cfg, DictConfig):
#         raise TypeError("Logger config must be a DictConfig!")
#
#     for _, lg_conf in logger_cfg.items():
#         if isinstance(lg_conf, DictConfig) and "_target_" in lg_conf:
#             log.info(f"Instantiating logger <{lg_conf._target_}>")
#             logger.append(hydra.utils.instantiate(lg_conf))
#
#     return logger
#
#
# @rank_zero_only
# def log_hyperparameters(object_dict: dict) -> None:
#     """Controls which config parts are saved by lightning loggers.
#
#     Additionally saves:
#     - Number of model parameters
#     """
#
#     hparams = {}
#
#     cfg = object_dict["cfg"]
#     model = object_dict["model"]
#     trainer = object_dict["trainer"]
#
#     if not trainer.logger:
#         log.warning("Logger not found! Skipping hyperparameter logging...")
#         return
#
#     hparams["model"] = cfg["model"]
#
#     # save number of model parameters
#     hparams["model/params/total"] = sum(p.numel() for p in model.parameters())
#     hparams["model/params/trainable"] = sum(
#         p.numel() for p in model.parameters() if p.requires_grad
#     )
#     hparams["model/params/non_trainable"] = sum(
#         p.numel() for p in model.parameters() if not p.requires_grad
#     )
#
#     hparams["datamodule"] = cfg["datamodule"]
#     hparams["trainer"] = cfg["trainer"]
#
#     hparams["callbacks"] = cfg.get("callbacks")
#     hparams["extras"] = cfg.get("extras")
#
#     hparams["task_name"] = cfg.get("task_name")
#     hparams["tags"] = cfg.get("tags")
#     hparams["ckpt_path"] = cfg.get("ckpt_path")
#     hparams["seed"] = cfg.get("seed")
#
#     # send hparams to all loggers
#     trainer.logger.log_hyperparams(hparams)
#
#
# def get_metric_value(metric_dict: dict, metric_name: str) -> float:
#     """Safely retrieves value of the metric logged in LightningModule."""
#
#     if not metric_name:
#         log.info("Metric name is None! Skipping metric value retrieval...")
#         return None
#
#     if metric_name not in metric_dict:
#         raise Exception(
#             f"Metric value not found! <metric_name={metric_name}>\n"
#             "Make sure metric name logged in LightningModule is correct!\n"
#             "Make sure `optimized_metric` name in `hparams_search` config is correct!"
#         )
#
#     metric_value = metric_dict[metric_name].item()
#     log.info(f"Retrieved metric value! <{metric_name}={metric_value}>")
#
#     return metric_value
#
#
# def close_loggers() -> None:
#     """Makes sure all loggers closed properly (prevents logging failure during multirun)."""
#
#     log.info("Closing loggers...")
#
#     if find_spec("wandb"):  # if wandb is installed
#         import wandb
#
#         if wandb.run:
#             log.info("Closing wandb!")
#             wandb.finish()
#
#
# def unflatten_wandb_config(dictionary):
#     resultDict = dict()
#     for key, value in dictionary.items():
#         parts = key.split("/")
#         d = resultDict
#         for part in parts[:-1]:
#             if part not in d:
#                 d[part] = dict()
#             d = d[part]
#         if isinstance(value, dict):
#             value = value["value"]
#         d[parts[-1]] = value
#     return resultDict
#
#
def get_latest_checkpoint(folder_path):
    """Returns path to the latest checkpoint in the folder."""

    if not os.path.exists(folder_path):
        raise Exception(f"Folder not found! <folder_path={folder_path}>")

    for root, _, files in os.walk(folder_path):
        checkpoints = [
            os.path.join(root, file) for file in files if file.endswith(".ckpt")
        ]
        if checkpoints:
            return max(checkpoints, key=os.path.getctime)


def get_config(folder_path):
    """Returns path to the config file in the folder."""

    if not os.path.exists(folder_path):
        raise Exception(f"Folder not found! <folder_path={folder_path}>")

    for root, _, files in os.walk(folder_path):
        if "config.yaml" in files and ".hydra" not in root:
            return os.path.join(root, "config.yaml")


def get_latest_checkpoint_and_config(folder_path):
    """Returns latest checkpoint and config from a folder."""
    checkpoint_path = None
    config_path = None

    if not os.path.exists(folder_path):
        log.warning(f"Folder path not found! <folder_path={folder_path}>")
        return checkpoint_path, config_path

    # get latest checkpoint
    checkpoint_path = get_latest_checkpoint(folder_path)

    if not checkpoint_path:
        log.error("Checkpoint not found!")
        raise Exception(f"Checkpoint not found! <folder_path={folder_path}>")

    # get config from checkpoint
    config_path = get_config(folder_path)

    if not config_path:
        log.error("Config not found!")
        # raise Exception(f"Config not found! <folder_path={folder_path}>")
        return checkpoint_path, config_path

    return checkpoint_path, config_path
