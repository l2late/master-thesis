import pytest

from domain.types import TrajectoryBatch
from infrastructure.lightning.datamodules.brcm_datamodule import (
    BRCMTrajectoryLitDataModule,
)

PAST_WINDOW = 5
MAX_HORIZON = 4
INITIAL_HORIZON = 1
NUM_ZONE_TEMPS = 2
NUM_HEAT_INPUTS = 2

FIELDS_WITH_MEASUREMENTS = {
    "past_ambient_temp",
    "past_zone_temps",
    "past_heat_inputs",
    "past_solar_rad",
    "future_ambient_temp",
    "future_zone_temps",
    "future_heat_inputs",
    "future_solar_rad",
}

FIELDS_WITH_TIMESTAMPS = {
    "past_timestamps",
    "future_timestamps",
}

EXPECTED_KEYS = FIELDS_WITH_MEASUREMENTS | FIELDS_WITH_TIMESTAMPS


@pytest.fixture()
def initialized_datamodule(five_room_csv):
    dm = BRCMTrajectoryLitDataModule(
        csv_file=five_room_csv,
        batch_size=2,
        size=40,
        window_size=2,
        max_horizon=2,
    )
    dm.setup()
    return dm


def make_datamodule(
    csv_file,
    batch_size=2,
    size=20,
    window_size=PAST_WINDOW,
    max_horizon=MAX_HORIZON,
    initial_horizon=INITIAL_HORIZON,
):
    return BRCMTrajectoryLitDataModule(
        csv_file=csv_file,
        batch_size=batch_size,
        size=size,
        window_size=window_size,
        max_horizon=max_horizon,
        initial_horizon=initial_horizon,
    )


def test_setup_with_window_plus_horizon_larger_than_size_fails(five_room_csv):
    datamodule = make_datamodule(
        csv_file=five_room_csv, batch_size=2, size=10, window_size=10, max_horizon=2
    )
    with pytest.raises(ValueError):
        datamodule.setup()


def test_batch_size_larger_than_size_fails(five_room_csv):
    datamodule = BRCMTrajectoryLitDataModule(
        csv_file=five_room_csv,
        batch_size=10,
        size=20,
        window_size=2,
        max_horizon=2,
    )
    with pytest.raises(ValueError):
        datamodule.setup()


def test_len_of_dataset(five_room_csv):
    size = 10
    datamodule = BRCMTrajectoryLitDataModule(
        csv_file=five_room_csv,
        batch_size=2,
        size=size,
        window_size=10,
        max_horizon=5,
    )
    assert len(datamodule.raw_dataset) == size


def test_batch_is_dict(initialized_datamodule):
    dm = initialized_datamodule
    train_loader = dm.train_dataloader()
    val_loader = dm.val_dataloader()
    train_batch = next(iter(train_loader))
    assert isinstance(train_batch, TrajectoryBatch)
    val_batch = next(iter(val_loader))
    assert isinstance(val_batch, TrajectoryBatch)


def test_batch_has_timestamp_field(initialized_datamodule):
    dm = initialized_datamodule
    loader = dm.train_dataloader()
    batch = next(iter(loader))

    _ = batch.future_timestamps
    _ = batch.past_timestamps

    assert len(batch.past_timestamps) == dm.window_size
    assert len(batch.future_timestamps) == dm.max_horizon


def test_timestamps_are_in_chronological_order(five_room_csv):
    """
    Test that the samples are in the right chronological order using the timestamps.
    """
    dm = BRCMTrajectoryLitDataModule(
        csv_file=five_room_csv,
        batch_size=1,
        size=20,
        window_size=2,
        max_horizon=2,
    )
    dm.setup()
    loader = dm.train_dataloader()
    batch = next(iter(loader))

    assert (batch.past_timestamps[:-1] <= batch.past_timestamps[1:]).all()
    assert (batch.future_timestamps[:-1] <= batch.future_timestamps[1:]).all()


def test_increasing_horizon_yields_targets_of_increasing_length(five_room_csv):
    batch_size = 4
    num_zone_temps = 5
    num_heat_inputs = 5

    dm = BRCMTrajectoryLitDataModule(
        csv_file=five_room_csv,
        batch_size=batch_size,
        size=100,
        window_size=PAST_WINDOW,
        max_horizon=MAX_HORIZON,
        initial_horizon=INITIAL_HORIZON,
    )

    current_horizon = INITIAL_HORIZON
    dm.setup()
    dataloader = dm.train_dataloader()
    batch = next(iter(dataloader))
    assert isinstance(batch, TrajectoryBatch)
    assert set(batch._fields) == EXPECTED_KEYS
    assert batch.past_zone_temps.shape == (
        batch_size,
        PAST_WINDOW,
        num_zone_temps,
    )  # (batch, seq_len, features)
    assert batch.future_zone_temps.shape == (
        batch_size,
        current_horizon + 1,
        num_zone_temps,
    )
    assert batch.past_heat_inputs.shape == (
        batch_size,
        PAST_WINDOW,
        num_heat_inputs,
    )
    assert batch.future_heat_inputs.shape == (
        batch_size,
        current_horizon + 1,
        num_heat_inputs,
    )
    assert batch.past_ambient_temp.shape == (
        batch_size,
        PAST_WINDOW,
        1,
    )
    assert batch.future_ambient_temp.shape == (
        batch_size,
        current_horizon + 1,
        1,
    )

    current_horizon = 3
    dm.update_horizon(current_horizon)
    dataloader = dm.train_dataloader()
    batch = next(iter(dataloader))
    assert isinstance(batch, TrajectoryBatch)
    assert set(batch._fields) == EXPECTED_KEYS
    time_dim_idx = 1  # (batch, seq_len, features)
    assert batch.past_zone_temps.shape[time_dim_idx] == PAST_WINDOW
    assert batch.future_zone_temps.shape[time_dim_idx] == current_horizon + 1
    assert batch.past_heat_inputs.shape[time_dim_idx] == PAST_WINDOW
    assert batch.future_heat_inputs.shape[time_dim_idx] == current_horizon + 1
    assert batch.past_ambient_temp.shape[time_dim_idx] == PAST_WINDOW
    assert batch.future_ambient_temp.shape[time_dim_idx] == current_horizon + 1


#### TEST LIST ####
