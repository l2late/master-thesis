import torch

from tests.fixtures.factories import make_batch

BATCH_SIZE = 2
WINDOW_SIZE = 3
HORIZON = 4
NUM_ROOMS = 5


import pytest


@pytest.fixture(scope="module")
def batch():
    return make_batch(
        batch_size=BATCH_SIZE,
        num_rooms=NUM_ROOMS,
        window_size=WINDOW_SIZE,
        horizon=HORIZON,
    )


def test_make_batch_is_dict(batch):
    assert isinstance(batch, dict), "Batch should be a dictionary."


def test_batch_contains_tensors(batch):
    for key, value in batch.items():
        assert isinstance(value, torch.Tensor), (
            f"Batch key '{key}' should contain a tensor."
        )


def test_batch_has_required_keys(batch):
    required_keys = [
        "past_zone_temps_traj",
        "past_heat_input_traj",
        "past_ambient_temp_traj",
        "measurement_traj_timestamps",
        "future_zone_temps_traj",
        "future_heat_input_traj",
        "future_ambient_temp_traj",
        "target_traj_timestamps",
    ]
    for key in required_keys:
        assert key in batch, f"Missing key: {key} in batch."


def test_batch_timestamps(batch):
    # zone temperatures
    expected_measurement_traj_timestamps = torch.tensor([0, 1, 2])
    # NOTE: there is overlap at t0: the last of measurements and first of targets
    expected_target_traj_timestamps = torch.tensor([2, 3, 4, 5, 6])
    assert torch.equal(
        batch["measurement_traj_timestamps"][0], expected_measurement_traj_timestamps
    ), "Measurement timestamps do not match expected values."
    assert torch.equal(
        batch["measurement_traj_timestamps"][1], expected_measurement_traj_timestamps
    ), "Measurement timestamps do not match expected values."
    assert torch.equal(
        batch["target_traj_timestamps"][0], expected_target_traj_timestamps
    ), "Target timestamps do not match expected values."
    assert torch.equal(
        batch["target_traj_timestamps"][1], expected_target_traj_timestamps
    ), "Target timestamps do not match expected values."


def test_batch_shapes(batch):
    # zone temperatures
    assert batch["past_zone_temps_traj"].shape == (
        BATCH_SIZE,
        WINDOW_SIZE,
        NUM_ROOMS,
    )
    assert batch["future_zone_temps_traj"].shape == (BATCH_SIZE, HORIZON + 1, NUM_ROOMS)

    # ambient temperatures
    assert batch["past_ambient_temp_traj"].shape == (
        BATCH_SIZE,
        WINDOW_SIZE,
        1,
    )
    assert batch["future_ambient_temp_traj"].shape == (BATCH_SIZE, HORIZON + 1, 1)

    # heat input
    assert batch["past_heat_input_traj"].shape == (
        BATCH_SIZE,
        WINDOW_SIZE,
        NUM_ROOMS,
    )
    assert batch["future_heat_input_traj"].shape == (BATCH_SIZE, HORIZON + 1, NUM_ROOMS)

    # timestamps
    assert batch["measurement_traj_timestamps"].shape == (BATCH_SIZE, WINDOW_SIZE)
    assert batch["target_traj_timestamps"].shape == (BATCH_SIZE, HORIZON + 1)


# def test_model_instatiation_with_partial():
#     model = make_model()
#     assert isinstance(model, torch.nn.Module), (
#         "Model should be an instance of torch.nn.Module."
#     )
