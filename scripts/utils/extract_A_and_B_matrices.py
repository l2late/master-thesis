from pathlib import Path

import lightning as L
import matplotlib.pyplot as plt
from hydra.utils import get_class
from omegaconf import OmegaConf

from src.utils.chooser import choose_run_dir


def main():
    runs_root = Path(
        "/home/l2late/stack/Master/Thesis/master-thesis-code/alpha_building_model/logs/"
    )

    # dynamically select checkpoint with TUI
    dir_path = choose_run_dir(runs_root)

    checkpoint = dir_path / "checkpoints" / "last.ckpt"
    config_path = dir_path / ".hydra" / "config.yaml"

    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint}")
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config: {config_path}")

    cfg = OmegaConf.load(config_path)

    if cfg.get("seed"):
        L.seed_everything(cfg.seed)

    model_cls = get_class(cfg.model._target_)
    init_kwargs = {k: v for k, v in cfg.model.items() if k != "_target_"}
    module = model_cls.load_from_checkpoint(str(checkpoint), **init_kwargs)

    # # Untrained Model
    # module = instantiate(cfg.model)
    A_matrix = module.dynamics.A_matrix.detach().cpu().numpy()
    # B_matrix = module.dynamics.B_matrix.detach().cpu().numpy()

    plt.imshow(A_matrix, cmap="viridis")
    plt.colorbar()
    plt.show()


if __name__ == "__main__":
    main()
