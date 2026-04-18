import numpy as np
import scipy.io
import torch

from alphabuilding.infrastructure.lightning.datamodules.brcm_datamodule import (
    BRCMTrajectoryLitDataModule,
)


def export_datamodule_to_matlab(
    datamodule: BRCMTrajectoryLitDataModule, output_path="system_id_data.mat"
):
    # 1. Run setup to generate splits, apply scaling, and populate data_tensors
    datamodule.setup("fit")
    datamodule.setup("test")  # Ensures test indices are populated

    # 2. Move continuous tensors to CPU and convert to numpy
    # We use .cpu().numpy() because data_tensors might be on the GPU
    tensors = {k: v.cpu().numpy() for k, v in datamodule.data_tensors.items()}

    # 3. Helper function to slice the continuous blocks and format Inputs (u) / Outputs (y)
    def extract_split(indices):
        if indices is None:
            return np.array([]), np.array([])

        start, end = indices
        if start == end:
            return np.array([]), np.array([])

        # y: Outputs (5 Zone Temperatures) -> Shape: [N, 5]
        y = tensors["zone_temps"][start:end]

        # u: Inputs -> Shape: [N, 7]
        # column_stack safely handles if ambient/solar are [N] or [N, 1]
        u = np.column_stack(
            [
                tensors["heat_input"][start:end],  # 5 columns
                tensors["ambient_temp"][start:end],  # 1 column
                tensors["solar_radiation"][start:end],  # 1 column
            ]
        )
        return u, y

    # 4. Extract continuous chunks
    u_train, y_train = extract_split(datamodule.train_indices)
    u_val, y_val = extract_split(datamodule.val_indices)
    y_test, y_test = extract_split(datamodule.test_indices)

    # 5. Save directly to a MATLAB .mat file
    mat_dict = {
        "u_train": u_train,
        "y_train": y_train,
        "u_val": u_val,
        "y_val": y_val,
        "u_test": y_test,
        "y_test": y_test,
        "Ts": 15,  # Sample time in minutes
    }

    scipy.io.savemat(output_path, mat_dict)
    print(f"Exported continuous data splits to {output_path}")
    print(f"Train samples: {u_train.shape[0]}, Val samples: {u_val.shape[0]}")
