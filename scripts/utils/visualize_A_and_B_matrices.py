from pathlib import Path

import lightning as L
from omegaconf import OmegaConf

from utils.chooser import choose_run_dir
from utils.instantiation import init_module_trained_from_cfg
from analysis.plot_dynamics_param_mapping import (
    visualize_dynamics_with_param_mapping,
)


def main():
    runs_root = Path(
        "/home/l2late/stack/Master/Thesis/master-thesis-code/alpha_building_model/logs/"
    )

    # dynamically select checkpoint with TUI
    dir_path = choose_run_dir(runs_root, auto_select_last=True)

    checkpoint = dir_path / "checkpoints" / "last.ckpt"
    config_path = dir_path / ".hydra" / "config.yaml"

    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint}")
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config: {config_path}")

    cfg = OmegaConf.load(config_path)

    # Seed deterministically if present in config (avoid static typing issues)
    seed = cfg.get("seed") if isinstance(cfg, dict) else None
    if seed is not None:
        L.seed_everything(int(seed))

    module = init_module_trained_from_cfg(cfg, checkpoint)

    # Visualize A/B with clear mapping to learned parameters
    visualize_dynamics_with_param_mapping(module.dynamics)


if __name__ == "__main__":
    main()
