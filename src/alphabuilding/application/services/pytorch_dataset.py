import torch
from torch.utils.data.dataset import Dataset as PyTorchDataset

from alphabuilding.application.services.brcm_dataset_creation_service import (
    BRCMDatasetCreationService,
)
from alphabuilding.domain.entities import Dataset as MyDataset
from alphabuilding.infrastructure.pytorch.datasets.trajectory_dataset import (
    PyTorchBRCMTrajectoryDataset,
)

# class BRCMTrajectoryDataset(PyTorchDataset):
#     """docstring for TimeseriesTrajectoryDataset."""
#
#     def __init__(self):
#         super(BRCMTrajectoryDataset, self).__init__()
#         self.dataset = BRCMDatasetCreationService().create_dataset(skip_data_rows=1000)
#
#     def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
#         # --- Assumptions on feature order ---
#         # Let's assume your get_scaled_window_as_numpy stacks features in this order:
#         # 1. Ambient Temp (1 feature)
#         # 2. Zone Temps (e.g., 4 features)
#         # 3. Heat Input (e.g., 4 features)
#         # Total features = 1 + 4 + 4 = 9
#
#         window_start = idx
#         window_end = idx + self.total_window_size
#
#         # 1. Get the entire window of scaled data as one NumPy array
#         full_window_np = self.dataset.get_scaled_window(window_start, window_end)
#
#         # 2. Slice the NumPy array into logical parts for the past and future
#         # These are efficient views, not copies
#         past_window = full_window_np[: self.input_window_size, :]
#         future_window = full_window_np[self.input_window_size :, :]
#
#         # 3. Create tensors for each part based on our assumed feature order
#         # Slicing the 'past' window
#         past_ambient_temp_traj = torch.from_numpy(past_window[:, 0:1]).float()
#         past_zone_temps_traj = torch.from_numpy(past_window[:, 1:5]).float()
#         past_heat_input_traj = torch.from_numpy(past_window[:, 5:9]).float()
#
#         # Slicing the 'future' window
#         future_ambient_temp_traj = torch.from_numpy(future_window[:, 0:1]).float()
#         future_zone_temps_traj = torch.from_numpy(future_window[:, 1:5]).float()
#         future_heat_input_traj = torch.from_numpy(future_window[:, 5:9]).float()
#
#         sample = {
#             # Inputs to the model
#             "past_ambient_temp_traj": past_ambient_temp_traj,
#             "past_zone_temps_traj": past_zone_temps_traj,
#             "past_heat_input_traj": past_heat_input_traj,
#             "future_ambient_temp_traj": future_ambient_temp_traj,  # e.g., known future weather
#             "future_heat_input_traj": future_heat_input_traj,  # e.g., known future control signals
#             # Target for the model to predict
#             "future_zone_temps_traj": future_zone_temps_traj,
#         }
#
#         return sample
