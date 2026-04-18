import numpy as np
import torch
from torch.utils.data.dataset import Dataset as PyTorchDataset

from alphabuilding.domain.entities import Dataset as MyDataset


class PyTorchBRCMTrajectoryDataset(PyTorchDataset):
    def __init__(
        self,
        custom_dataset: MyDataset,
        past_window_size: int,
        max_future_horizon_size: int,
        current_future_horizon_size: int | None = None,
    ):
        super().__init__()
        self.dataset = custom_dataset
        self.past_window_size = past_window_size
        self.max_future_horizon_size = max_future_horizon_size
        if current_future_horizon_size is None:
            self.current_future_horizon_size = max_future_horizon_size
        else:
            self.current_future_horizon_size = current_future_horizon_size
        self.max_total_window_size = past_window_size + max_future_horizon_size
        self.current_total_window_size = (
            past_window_size + self.current_future_horizon_size
        )

        if self.max_future_horizon_size < self.current_future_horizon_size:
            raise ValueError(
                f"Maximum future horizon size {self.max_future_horizon_size} is less than "
                f"current future horizon size {self.current_future_horizon_size}. "
                "Please adjust the maximum future horizon size."
            )

        if self.max_total_window_size >= len(self.dataset):
            raise ValueError(
                f"Maximum total window size {self.max_total_window_size} exceeds dataset length "
                f"{len(self.dataset)}. Please adjust the past window size and/or maximum future horizon size."
            )

    @property
    def current_horizon(self) -> int:
        """
        Get the current future horizon size.
        This is the number of future time steps to predict.
        """
        return self.current_future_horizon_size

    def update_current_horizon(self, new_horizon: int) -> None:
        """
        Set the current future horizon size.
        This allows for dynamic adjustment of the prediction horizon.
        """
        if new_horizon > self.max_future_horizon_size:
            raise ValueError(
                f"New horizon {new_horizon} exceeds maximum future horizon size {self.max_future_horizon_size}."
            )
        self.current_future_horizon_size = new_horizon
        self.current_total_window_size = (
            self.past_window_size + self.current_future_horizon_size
        )
        print(f"\n--- PYTORCH DATASET Horizon updated to {new_horizon} ---")

    @property
    def max_horizon(self) -> int:
        """
        Get the maximum future horizon size.
        This is the maximum number of future time steps that can be predicted.
        """
        return self.max_future_horizon_size

    def __len__(self) -> int:
        return len(self.dataset) - self.max_total_window_size

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        """Get a data sample for the given index.
        Note that there is overlap at t0 between past and future trajectories.
        past trajectories include timesteps     [t_{-W}, ..., t0]
        future trajectories include timesteps   [t0, ..., t_H]
        Why? for consistency and flexibility: all data available in the trajectories
        Care must be taken to index correctly.
        For example, the target zone temperatures need to be from t1 to t_H
        while the heat input and ambient temperatures need to be from t0 to t_H-1

            past trajectories
        [ t_{-W}    ...     t0 ]
                            future trajectories
                          [ t0 ... t_{H-1} t_{H} ]
        """
        past_start = idx
        past_end = idx + self.past_window_size
        # NOTE: the -1 to make sure t0 is
        future_start = past_end - 1
        # NOTE: the +1 is to compensate the shifted starting point
        future_end = future_start + self.current_future_horizon_size + 1

        t_W_to_t0_dict = self.dataset.get_scaled_window(past_start, past_end)
        t_W_to_t0_timestamps = self.dataset.get_timestamps(past_start, past_end).astype(
            np.int64
        )

        t0_to_tH_dict = self.dataset.get_scaled_window(future_start, future_end)
        t0_to_tH_timestamps = self.dataset.get_timestamps(
            future_start, future_end
        ).astype(np.int64)

        sample = {
            "past_ambient_temp_traj": torch.from_numpy(
                t_W_to_t0_dict["ambient_temp"]
            ).float(),
            "past_zone_temps_traj": torch.from_numpy(
                t_W_to_t0_dict["zone_temps"]
            ).float(),
            "past_heat_input_traj": torch.from_numpy(
                t_W_to_t0_dict["heat_input"]
            ).float(),
            "future_ambient_temp_traj": torch.from_numpy(
                t0_to_tH_dict["ambient_temp"]
            ).float(),
            "future_heat_input_traj": torch.from_numpy(
                t0_to_tH_dict["heat_input"]
            ).float(),
            "future_zone_temps_traj": torch.from_numpy(
                t0_to_tH_dict["zone_temps"]
            ).float(),
            "measurement_traj_timestamps": torch.tensor(
                t_W_to_t0_timestamps, dtype=torch.long
            ),
            "target_traj_timestamps": torch.tensor(
                t0_to_tH_timestamps, dtype=torch.long
            ),
        }

        return sample
