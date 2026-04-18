import os
from pathlib import Path


def get_latest_ckpt_path(dir_path: Path) -> Path:
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory {dir_path} does not exist.")
    # only files that end with .ckpt
    ckpt_files = list(dir_path.glob("*.ckpt"))
    latest_ckpt_path = sorted(ckpt_files, key=os.path.getmtime, reverse=True)[0]
    # print(f"Latest model found: {latest_ckpt_path}")
    assert latest_ckpt_path.suffix == ".ckpt", "Latest model is not a checkpoint file."
    return latest_ckpt_path
