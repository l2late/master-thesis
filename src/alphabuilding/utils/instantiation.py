from pathlib import Path

import lightning as L
from hydra.utils import get_class, instantiate
from omegaconf import OmegaConf

from alphabuilding.utils.chooser import choose_run_dir
from alphabuilding.utils.paths import paths


def init_module_trained_from_cfg(cfg: OmegaConf, checkpoint: Path) -> L.LightningModule:
    model_cls = get_class(cfg.model._target_)
    model_cfg = cfg.model
    dynamics = instantiate(model_cfg.dynamics)

    init_kwargs = {k: v for k, v in model_cfg.items() if k != "_target_"}

    init_kwargs["dynamics"] = dynamics

    module = model_cls.load_from_checkpoint(
        str(checkpoint), strict=False, weights_only=False, **init_kwargs
    ).eval()
    return module


def get_last_module_and_datamodule_from_checkpoint(auto_select_last: bool = False):
    # dynamically select checkpoint with TUI
    dir_path = choose_run_dir(paths.log_dir, auto_select_last=auto_select_last)

    checkpoint = dir_path / "checkpoints" / "last.ckpt"
    config_path = dir_path / ".hydra" / "config.yaml"

    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint}")
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config: {config_path}")

    cfg = OmegaConf.load(config_path)

    cfg.paths = paths
    cfg.datamodule.batch_size = 1
    cfg.datamodule.num_workers = 1

    if cfg.get("seed"):
        L.seed_everything(cfg.seed)

    module = init_module_trained_from_cfg(cfg, checkpoint)
    datamodule: L.LightningDataModule = instantiate(cfg.datamodule)
    return module, datamodule
