import pytest
import torch
from torch.utils.data import DataLoader

from application.services.brcm_dataset_creation_service import (
    BRCMDatasetCreationService,
)
from infrastructure.pytorch.datasets.trajectory_dataset import (
    PyTorchBRCMTrajectoryDataset,
)

PAST_WINDOW = 30
MAX_HORIZON = 7
CURRENT_HORIZON = 3
NUM_ZONE_TEMPS = 5
NUM_HEAT_INPUTS = 5

KEYS_WITH_MEASUREMENTS = {
    "past_ambient_temp_traj",
    "past_zone_temps_traj",
    "past_heat_input_traj",
    "future_ambient_temp_traj",
    "future_zone_temps_traj",
    "future_heat_input_traj",
}

KEYS_WITH_TIMESTAMPS = {
    "measurement_traj_timestamps",
    "target_traj_timestamps",
}

EXPECTED_KEYS = KEYS_WITH_MEASUREMENTS | KEYS_WITH_TIMESTAMPS


@pytest.fixture(scope="module")
def brcm_dataset_full(five_room_csv):
    service = BRCMDatasetCreationService()
    return service.create_dataset(csv_file=five_room_csv)


@pytest.fixture(scope="module")
def brcm_dataset_10(five_room_csv):
    service = BRCMDatasetCreationService()
    return service.create_dataset(csv_file=five_room_csv, nrows=10)


@pytest.fixture(scope="module")
def train_dataset(brcm_dataset_full):
    train_dataset = brcm_dataset_full.split(train_ratio=0.6)
    return train_dataset


@pytest.fixture(scope="module")
def train_dataset_6(brcm_dataset_10):
    train_dataset = brcm_dataset_10.split(train_ratio=0.6)
    return train_dataset


@pytest.fixture(scope="module")
def train_pytorch_traj_dataset(train_dataset):
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
        current_future_horizon_size=CURRENT_HORIZON,
    )
    return pytorch_traj_dataset


def test_len(train_dataset):
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
        current_future_horizon_size=CURRENT_HORIZON,
    )
    assert len(pytorch_traj_dataset) == len(train_dataset) - PAST_WINDOW - MAX_HORIZON


def test_len_of_split(train_dataset_6):
    assert len(train_dataset_6) == 6


def test_window_plus_horizon_larger_than_length_fails(train_dataset_6):
    with pytest.raises(ValueError):
        _ = PyTorchBRCMTrajectoryDataset(
            custom_dataset=train_dataset_6,
            past_window_size=PAST_WINDOW,
            max_future_horizon_size=MAX_HORIZON,
            current_future_horizon_size=CURRENT_HORIZON,
        )


def test_sample_is_dict(train_dataset):
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
        current_future_horizon_size=CURRENT_HORIZON,
    )
    sample = pytorch_traj_dataset[0]
    assert isinstance(sample, dict)


def test_sample_has_correct_keys(train_dataset):
    """Tests that the dictionary has all the expected keys and no more."""
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
        current_future_horizon_size=CURRENT_HORIZON,
    )
    sample = pytorch_traj_dataset[0]
    assert set(sample.keys()) == EXPECTED_KEYS


def test_sample_values_are_tensors(train_dataset):
    """Tests that every value in the dictionary is a PyTorch tensor."""
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
        current_future_horizon_size=CURRENT_HORIZON,
    )
    sample = pytorch_traj_dataset[0]

    for key, value in sample.items():
        assert isinstance(value, torch.Tensor), f"Value for key '{key}' is not a Tensor"
        if key in KEYS_WITH_MEASUREMENTS:
            assert value.dtype == torch.float32, (
                f"Tensor for key '{key}' is not float32"
            )
        elif key in KEYS_WITH_TIMESTAMPS:
            assert value.dtype == torch.long, f"Tensor for key '{key}' is not long"


def test_sample_tensor_shapes_are_correct_length_when_current_horizon_not_provided(
    train_dataset,
):
    """
    Tests that each tensor in the dictionary has the correct shape.
    """
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
    )
    sample = pytorch_traj_dataset[0]

    expected_shapes = {
        "past_ambient_temp_traj": (PAST_WINDOW, 1),
        "past_zone_temps_traj": (PAST_WINDOW, NUM_ZONE_TEMPS),
        "past_heat_input_traj": (PAST_WINDOW, NUM_HEAT_INPUTS),
        "future_ambient_temp_traj": (MAX_HORIZON + 1, 1),
        "future_zone_temps_traj": (MAX_HORIZON + 1, NUM_ZONE_TEMPS),
        "future_heat_input_traj": (MAX_HORIZON + 1, NUM_HEAT_INPUTS),
        "measurement_traj_timestamps": (PAST_WINDOW,),
        "target_traj_timestamps": (MAX_HORIZON + 1,),
    }

    for key, expected_shape in expected_shapes.items():
        assert key in sample, f"Key '{key}' is missing from the sample"
        assert sample[key].shape == expected_shape, (
            f"Shape for '{key}' is wrong. Got {sample[key].shape}, expected {expected_shape}"
        )


def test_sample_tensor_shapes_are_current_horizon_length(train_dataset):
    """
    Tests that each tensor in the dictionary has the correct shape.
    """
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
        current_future_horizon_size=CURRENT_HORIZON,
    )
    sample = pytorch_traj_dataset[0]

    expected_shapes = {
        # Past data should have length INPUT_WINDOW
        "past_ambient_temp_traj": (PAST_WINDOW, 1),
        "past_zone_temps_traj": (PAST_WINDOW, NUM_ZONE_TEMPS),
        "past_heat_input_traj": (PAST_WINDOW, NUM_HEAT_INPUTS),
        # Future data should have length TARGET_WINDOW
        "future_ambient_temp_traj": (CURRENT_HORIZON + 1, 1),
        "future_zone_temps_traj": (CURRENT_HORIZON + 1, NUM_ZONE_TEMPS),
        "future_heat_input_traj": (CURRENT_HORIZON + 1, NUM_HEAT_INPUTS),
        # Timestamps should have length INPUT_WINDOW + TARGET_WINDOW
        "measurement_traj_timestamps": (PAST_WINDOW,),
        "target_traj_timestamps": (CURRENT_HORIZON + 1,),
    }

    for key, expected_shape in expected_shapes.items():
        assert key in sample, f"Key '{key}' is missing from the sample"
        assert sample[key].shape == expected_shape, (
            f"Shape for '{key}' is wrong. Got {sample[key].shape}, expected {expected_shape}"
        )


@pytest.mark.skip(reason="this worked for MinMaxScaler, but now using StandardScaler")
def test_all_tensors_are_between_0_1_and_0_9(train_dataset):
    """
    Tests that all tensor values are between 0.1 and 0.9.
    """
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
    )
    sample = pytorch_traj_dataset[0]

    for key, tensor in sample.items():
        if key in KEYS_WITH_MEASUREMENTS:
            assert torch.all(tensor >= 0.1) and torch.all(tensor <= 0.9), (
                f"Values for key '{key}' are not in the range [0.1, 0.9]"
            )


def test_dataloader_batch_structure(train_dataset):
    pytorch_traj_dataset = PyTorchBRCMTrajectoryDataset(
        custom_dataset=train_dataset,
        past_window_size=PAST_WINDOW,
        max_future_horizon_size=MAX_HORIZON,
    )
    batch_size = 4
    dataloader = DataLoader(pytorch_traj_dataset, batch_size=batch_size)
    batch = next(iter(dataloader))
    assert isinstance(batch, dict)

    assert set(batch.keys()) == EXPECTED_KEYS

    assert batch["past_zone_temps_traj"].shape == (
        batch_size,
        PAST_WINDOW,
        NUM_ZONE_TEMPS,
    )  # (batch, seq_len, features)
    assert batch["future_zone_temps_traj"].shape == (
        batch_size,
        MAX_HORIZON + 1,
        NUM_ZONE_TEMPS,
    )
    assert batch["past_heat_input_traj"].shape == (
        batch_size,
        PAST_WINDOW,
        NUM_HEAT_INPUTS,
    )
    assert batch["future_heat_input_traj"].shape == (
        batch_size,
        MAX_HORIZON + 1,
        NUM_HEAT_INPUTS,
    )
    assert batch["past_ambient_temp_traj"].shape == (
        batch_size,
        PAST_WINDOW,
        1,
    )
    assert batch["future_ambient_temp_traj"].shape == (
        batch_size,
        MAX_HORIZON + 1,
        1,
    )
