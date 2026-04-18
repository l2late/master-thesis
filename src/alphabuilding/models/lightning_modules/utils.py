from pathlib import Path

import lightning as L
import numpy as np
import torch
from lightning_utilities.core.apply_func import apply_to_collection


def save_plotting_data_to_npz(path: Path, data: dict[str, np.ndarray]):
    timestamps = data["timestamps"]
    preds = data["preds"]
    targets = data["target_temps"]
    ambient_temps = data["ambient_temps"]
    heat_inputs = data["heat_inputs"]

    np.savez(
        path,
        timestamps=timestamps,
        preds=preds,
        targets=targets,
        ambient_temps=ambient_temps,
        heat_inputs=heat_inputs,
    )


def direct_multi_stepping_prediction(
    module: L.LightningModule,
    dataloader,
    start_idx: int = 0,
) -> dict:
    if start_idx < 0:
        raise ValueError("Start index must be non-negative.")

    dataloader_iter = iter(dataloader)
    for _ in range(start_idx):
        try:
            next(dataloader_iter)
        except StopIteration:
            raise ValueError(f"Start position {start_idx} exceeds dataloader length")

    module.eval()
    # device = "cuda"
    device = module.device
    module.to(device)

    results = []
    with torch.no_grad():
        batch = next(dataloader_iter)
        # batch = {
        #     k: v.to(device) for k, v in batch.items()
        # }  # this doesn't work anymore, because it not a dict but a namedtuple
        # batch.to(device)  # this doesn't work for namedtuples
        batch = apply_to_collection(batch, torch.Tensor, lambda t: t.to(device))
        batch_size = batch.past_ambient_temp.shape[0]
        output = module.predict_step(batch, batch_idx=0)

        initial_states, _, _, _ = module._estimate_initial_states(batch, batch_size)

    return output, initial_states, batch
