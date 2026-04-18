import pytest
import torch

from tests.fixtures.factories import make_batch, make_model

BATCH_SIZE = 1
WINDOW_SIZE = 3
HORIZON = 10
STEPS = HORIZON + 1
NUM_ROOMS = 5
NUM_STATES = NUM_ROOMS * 2


@pytest.fixture()
def module(device="cuda"):
    return make_model(
        num_mass_states_per_zone=1,
        horizon=HORIZON,
        num_zones=NUM_ROOMS,
    ).to(device)


@pytest.fixture
def batch():
    return make_batch(
        batch_size=BATCH_SIZE,
        num_rooms=NUM_ROOMS,
        window_size=WINDOW_SIZE,
        horizon=HORIZON,
        device="cuda",
    )


@pytest.fixture
def module_predict_output(module, batch):
    return module.predict_step(batch, batch_idx=0)


def test_module_training_step_returns_tensor(module, batch):
    output = module.training_step(batch, batch_idx=0)
    assert isinstance(output, torch.Tensor), "Training step output should be a tensor"


def test_module_predict_step_is_dict(module_predict_output):
    assert isinstance(module_predict_output, dict), "Output should be a dictionary."


def test_module_test_predict_step_output_has_right_keys(module_predict_output):
    REQUIRED_TEST_OUTPUT_KEYS = [
        "preds",
        "target_temps",
        "ambient_temps",
        "heat_inputs",
        "timestamps",
        "hidden_states",
    ]

    for key in REQUIRED_TEST_OUTPUT_KEYS:
        assert key in module_predict_output, f"Missing key: {key} in test step output."


def test_module_predict_step_output_shapes(module_predict_output):
    if BATCH_SIZE == 1:
        assert len(module_predict_output["timestamps"]) == STEPS, (
            "Timestamps length mismatch."
        )
        assert module_predict_output["timestamps"].shape == (STEPS,), (
            "Timestamps shape mismatch."
        )
        assert module_predict_output["preds"].shape == (
            STEPS,
            NUM_ROOMS,
        ), "Predictions shape mismatch."
        assert module_predict_output["target_temps"].shape == (
            STEPS,
            NUM_ROOMS,
        ), "Target temperatures shape mismatch."
        assert module_predict_output["ambient_temps"].shape == (
            STEPS,
            1,
        ), "Ambient temperatures shape mismatch."
        assert module_predict_output["heat_inputs"].shape == (
            STEPS,
            NUM_ROOMS,
        ), "Heat inputs shape mismatch."
        assert module_predict_output["hidden_states"].shape == (
            STEPS,
            NUM_ROOMS,  # Assuming 1 mass states per zone
        ), "Hidden states shape mismatch."
    else:
        raise ValueError(
            "The test step currently assumes a batch size of 1 for simplicity."
        )


def test_module_forward(module, batch):
    x0 = torch.rand((1, NUM_STATES), device="cuda")  # B x N
    u = batch["future_heat_input_traj"]  # B x T x 5
    d = batch["future_ambient_temp_traj"]  # B x T x 1
    t_eval = torch.linspace(0, HORIZON, STEPS, device="cuda")
    states_trajectory = module(x0, t_eval, u, d)
    assert states_trajectory.shape == (STEPS, BATCH_SIZE, NUM_STATES)
