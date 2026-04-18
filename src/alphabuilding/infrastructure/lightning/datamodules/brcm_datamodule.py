from pathlib import Path

import lightning as L
import numpy as np
import torch
from sklearn.base import TransformerMixin
from torch.utils.data import DataLoader as TorchDataLoader

from alphabuilding.application.services.brcm_dataset_creation_service import (
    BRCMDatasetCreationService,
)
from alphabuilding.domain.types import Scaler, TrajectoryBatch


class BRCMTrajectoryLitDataModule(L.LightningDataModule):
    def __init__(
        self,
        csv_file: Path,
        batch_size: int,
        num_workers: int = 0,
        size: int | None = None,
        device: str = "cuda",
        train_ratio: float = 0.2,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        pin_memory: bool = False,
        window_size: int = 72,
        initial_horizon: int = 2,
        max_horizon: int = 4,
        # Format: [noise_std_temp, noise_std_solar_rad] #TODO: Consider using a dict or dataclass for clarity
        noise_stds: list[float] = [0.0, 0.0],
    ):
        super().__init__()
        # VALIDATION: Ensure we have exactly two values
        if len(noise_stds) != 2:
            raise ValueError(
                f"noise_stds must be a list of exactly 2 floats [temp_noise, solar_noise], "
                f"got {len(noise_stds)} values: {noise_stds}"
            )

        self.noise_std_temp, self.noise_std_solar_rad = noise_stds
        # Will be calculated after scalers are fitted
        self.scaled_noise_std_solar_rad, self.scaled_noise_std_temp = (
            None,
            None,
        )

        self.save_hyperparameters()
        self.device = device
        self.window_size = window_size
        self.max_horizon = max_horizon
        self.initial_horizon = initial_horizon
        self.current_horizon = initial_horizon
        self.size = size
        self.batch_size = batch_size
        self.raw_dataset = BRCMDatasetCreationService().create_dataset(
            csv_file=csv_file,
            nrows=self.size,
        )
        self.num_workers = num_workers
        self.pin_memory = pin_memory
        self.shuffle_training_set = True
        self.persistent_workers = False

        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

        self.train_split = None
        self.val_split = None
        self.test_split = None

        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None

        # data tensors (populated in setup)
        self.data_tensors = {}
        self.timestamps = None

        # Split indices for efficient slicing
        self.train_indices = None
        self.val_indices = None
        self.test_indices = None

    @property
    def zone_temp_scaler(self) -> Scaler:
        """
        Returns the fitted scaler for the zone temperatures.
        This property should only be accessed after `datamodule.setup()` has been called.
        """
        try:
            zone_temps_fg = self.raw_dataset.get_feature_group("zone_temps")
            if not zone_temps_fg.scaler_is_fitted:
                raise RuntimeError(
                    "Scaler is not fitted. Call datamodule.setup('fit') first."
                )
            return zone_temps_fg.scaler
        except Exception as e:
            raise RuntimeError("Failed to retrieve the zone temperature scaler.") from e

    @property
    def ambient_temp_scaler(self) -> TransformerMixin:
        """
        Returns the fitted scaler for the ambient temperature.
        This property should only be accessed after `datamodule.setup()` has been called.
        """
        try:
            ambient_temp_fg = self.raw_dataset.get_feature_group("ambient_temp")
            if not ambient_temp_fg.scaler_is_fitted:
                raise RuntimeError(
                    "Scaler is not fitted. Call datamodule.setup('fit') first."
                )
            return ambient_temp_fg.scaler
        except Exception as e:
            raise RuntimeError(
                "Failed to retrieve the ambient temperature scaler."
            ) from e

    @property
    def heat_input_scaler(self) -> TransformerMixin:
        """
        Returns the fitted scaler for the heat input
        This property should only be accessed after `datamodule.setup()` has been called.
        """
        try:
            heat_inputs_fg = self.raw_dataset.get_feature_group("heat_input")
            if not heat_inputs_fg.scaler_is_fitted:
                raise RuntimeError(
                    "Scaler is not fitted. Call datamodule.setup('fit') first."
                )
            return heat_inputs_fg.scaler
        except Exception as e:
            raise RuntimeError("Failed to retrieve the heat input scaler.") from e

    @property
    def solar_radiation_scaler(self) -> TransformerMixin:
        """
        Returns the fitted scaler for the solar radiation.
        This property should only be accessed after `datamodule.setup()` has been called.
        """
        try:
            solar_radiation_fg = self.raw_dataset.get_feature_group("solar_radiation")
            if not solar_radiation_fg.scaler_is_fitted:
                raise RuntimeError(
                    "Scaler is not fitted. Call datamodule.setup('fit') first."
                )
            return solar_radiation_fg.scaler
        except Exception as e:
            raise RuntimeError("Failed to retrieve the solar radiation scaler.") from e

    def update_horizon(self, horizon: int) -> None:
        """
        Update the current future horizon size.
        This allows for dynamic adjustment of the prediction horizon.
        """
        if horizon > self.max_horizon:
            raise ValueError(
                f"New horizon {horizon} exceeds maximum future horizon size {self.max_horizon}."
            )
        self.current_horizon = horizon
        print(f"\n--- PYTORCH DATASET Horizon updated to {horizon} ---")

    def _compute_scaled_noise_stds(self) -> None:
        """Compute noise stds in scaled space. Requires scalers to be fitted."""
        self.scaled_noise_std_temp = self.noise_std_temp / self.zone_temp_scaler.scale_
        self.scaled_noise_std_solar_rad = (
            self.noise_std_solar_rad / self.solar_radiation_scaler.scale_
        )

    def setup(self, stage=None):
        # 1. Split the dataset (CPU operations)
        self.train_split, self.val_split, self.test_split = self.raw_dataset.split(
            train_ratio=self.train_ratio,
            val_ratio=self.val_ratio,
            test_ratio=self.test_ratio,
        )

        self._compute_scaled_noise_stds()

        self._validate_split(self.train_split)
        self._validate_split(self.val_split)
        self._validate_split(self.test_split)

        train_len = len(self.train_split)
        val_len = len(self.val_split)
        test_len = len(self.test_split)

        self.train_indices = (0, train_len)
        self.val_indices = (train_len, train_len + val_len)
        self.test_indices = (
            train_len + val_len,
            train_len + val_len + test_len,
        )

        self._prepare_data_tensors()
        print(f"Setup complete. Train: {train_len}, Val: {val_len}, Test: {test_len}")

    def _prepare_data_tensors(self):
        """Prepares dataset tensors on the configured device (CPU or GPU)."""
        target_device = torch.device(self.device)
        print(f"Preparing dataset tensors on {target_device}...")

        total_length = len(self.raw_dataset)
        full_scaled_data = self.raw_dataset.get_scaled_window(0, total_length)

        full_timestamps = self.raw_dataset.get_timestamps(
            0, total_length
        ).values.astype(np.int64)

        target_dtype = torch.get_default_dtype()
        tensor_keys = ["ambient_temp", "zone_temps", "heat_input", "solar_radiation"]

        # Load directly to the target device
        self.data_tensors = {
            key: torch.tensor(
                full_scaled_data[key], dtype=target_dtype, device=target_device
            )
            for key in tensor_keys
        }

        self.timestamps = torch.from_numpy(full_timestamps).long().to(target_device)

        if target_device.type == "cpu":
            print("Moved dataset to CPU Memory")
        if target_device.type == "cuda":
            print(
                f"GPU Memory: {torch.cuda.memory_allocated(target_device) / 1024**2:.2f} MB"
            )

    def train_dataloader(self):
        return self._dataloader(self.train_indices, shuffle=True)

    def val_dataloader(self):
        return self._dataloader(self.val_indices, shuffle=False)

    def test_dataloader(self):
        # return self._dataloader(self.test_indices, shuffle=False, batch_size=1)
        return self._dataloader(self.test_indices, shuffle=False)

    def _dataloader(self, split_indices, shuffle=False, batch_size=None):
        dataset = InMemoryTrajectoryDataset(
            data_tensors=self.data_tensors,
            timestamps=self.timestamps,
            split_indices=split_indices,
            window_size=self.window_size,
            current_horizon=self.current_horizon,
            max_horizon=self.max_horizon,
            scaled_noise_std_temp=self.scaled_noise_std_temp,
            scaled_noise_std_solar_rad=self.scaled_noise_std_solar_rad,
        )
        return TorchDataLoader(
            dataset,
            batch_size=batch_size or self.batch_size,
            num_workers=0,  # No multiprocessing for GPU data
            shuffle=shuffle,
            pin_memory=False,  # Data already on GPU
        )

    def _validate_split(self, split):
        if len(split) < self.window_size + self.max_horizon:
            raise ValueError(
                f"Dataset split size {len(split)} is smaller than "
                f"window size {self.window_size} + horizon {self.max_horizon}. "
                "Please adjust the dataset size or the window and max_horizon sizes."
            )
        if len(split) < self.batch_size:
            raise ValueError(
                f"Dataset split size {len(split)} is smaller than "
                f"batch size {self.batch_size}. Please adjust the dataset size or the batch size."
            )


class InMemoryTrajectoryDataset(torch.utils.data.Dataset):
    """Dataset using efficient tensor slicing (works for both CPU and GPU)."""

    def __init__(
        self,
        data_tensors: dict[str, torch.Tensor],
        timestamps: torch.Tensor,
        split_indices: tuple[int, int],
        window_size: int,
        current_horizon: int,
        max_horizon: int,
        scaled_noise_std_temp: float,
        scaled_noise_std_solar_rad: float,
    ):
        self.device = data_tensors["zone_temps"].device
        self.data_tensors = data_tensors
        self.timestamps = timestamps
        self.split_start, self.split_end = split_indices
        self.window_size = window_size
        self.current_horizon = current_horizon
        self.max_horizon = max_horizon
        self.scaled_noise_std_temp = torch.tensor(
            scaled_noise_std_temp, device=self.device
        )
        self.scaled_noise_std_solar_rad = torch.tensor(
            scaled_noise_std_solar_rad, device=self.device
        )

        split_length = self.split_end - self.split_start
        # max horizon is useful when doing curriculum learning and adjusting horizon during training,
        # ensures we never sample out of bounds.
        self.num_trajectories = max(
            0, split_length - self.window_size - self.max_horizon + 1
        )

    def __len__(self):
        return self.num_trajectories

    def __getitem__(self, idx) -> TrajectoryBatch:
        abs_idx = self.split_start + idx

        p_start = abs_idx
        p_end = abs_idx + self.window_size

        # NOTE: f_start is one step before p_end to ensure continuity between past and future
        # so both past and future include t=0 at the boundary
        # i.e. last step of past is t=0, first step of future is t=0)
        f_start = p_end - 1
        f_end = f_start + self.current_horizon + 1

        data = self.data_tensors

        # clean slices
        past_zone_temps = data["zone_temps"][p_start:p_end]
        future_zone_temps = data["zone_temps"][f_start:f_end]

        past_ambient_temp = data["ambient_temp"][p_start:p_end]
        future_ambient_temp = data["ambient_temp"][f_start:f_end]

        past_solar_rad = data["solar_radiation"][p_start:p_end]
        future_solar_rad = data["solar_radiation"][f_start:f_end]

        # add noise only to past (input) features
        if self.scaled_noise_std_temp > 0:
            past_zone_temps = (
                past_zone_temps
                + torch.randn_like(
                    past_zone_temps,
                )
                * self.scaled_noise_std_temp
            )

            past_ambient_temp = (
                past_ambient_temp
                + torch.randn_like(past_ambient_temp) * self.scaled_noise_std_temp
            )

        if self.scaled_noise_std_solar_rad > 0:
            past_solar_rad = (
                past_solar_rad
                + torch.randn_like(past_solar_rad) * self.scaled_noise_std_solar_rad
            ).clamp(min=0.0)

        return TrajectoryBatch(
            past_ambient_temp=past_ambient_temp,
            past_zone_temps=past_zone_temps,
            past_heat_inputs=data["heat_input"][p_start:p_end],
            past_solar_rad=past_solar_rad,
            future_ambient_temp=future_ambient_temp,
            future_heat_inputs=data["heat_input"][f_start:f_end],
            future_zone_temps=future_zone_temps,
            future_solar_rad=future_solar_rad,
            past_timestamps=self.timestamps[p_start:p_end],
            future_timestamps=self.timestamps[f_start:f_end],
        )
