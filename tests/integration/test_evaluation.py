from functools import partial

import numpy as np
import pytest
import torch

from infrastructure.lightning.datamodules.brcm_datamodule import (
    BRCMTrajectoryLitDataModule,
)
from infrastructure.lightning.modules.neural_ode import (
    LitMultiStepNeuralSSNODEModule,
)
from models.lightning_modules.evaluation import format_predictions_tensor_dict_to_numpy
from models.lightning_modules.utils import direct_multi_stepping_prediction

TEST_RESULTS_REQUIRED_KEYS = [
    "timestamps",
    "preds",
    "target_temps",
    "ambient_temps",
    "heat_inputs",
]

BATCH_SIZE = 1
WINDOW_SIZE = 2
HORIZON = 2
NUM_ROOMS = 5


@pytest.fixture(scope="module")
def dataloader(five_room_csv):
    dm = BRCMTrajectoryLitDataModule(
        csv_file=five_room_csv,
        size=10,
        train_ratio=0.1,
        val_ratio=0.1,
        test_ratio=0.8,
        batch_size=BATCH_SIZE,
        window_size=WINDOW_SIZE,
        max_horizon=HORIZON,
        num_workers=0,
    )
    dm.setup("test")
    test_dataloader = dm.test_dataloader()
    return test_dataloader


@pytest.fixture(scope="module")
def trained_module(device="cpu"):
    """
    Loads a trained LitMultiStepNeuralSSNODEModule from a checkpoint,
    providing the required partial optimizer and scheduler.
    """
    ckpt_path = "tests/data/model_checkpoints/ss_node-epoch=3994-val_multi_step_loss=0.00333814.ckpt"

    optimizer_partial = partial(torch.optim.Adam)
    lr_scheduler_partial = partial(torch.optim.lr_scheduler.ReduceLROnPlateau)

    model = LitMultiStepNeuralSSNODEModule.load_from_checkpoint(
        ckpt_path,
        optimizer=optimizer_partial,
        lr_scheduler=lr_scheduler_partial,
        num_mass_states_per_zone=15,
        horizon=HORIZON,
        strict=False,
    )

    return model.to(device)


@pytest.fixture(scope="module")
def results(dataloader, trained_module):
    return direct_multi_stepping_prediction(
        module=trained_module, dataloader=dataloader, start_idx=0
    )


@pytest.fixture(scope="module")
def plotting_data(results):
    return format_predictions_tensor_dict_to_numpy(results)


def test_results_are_dict(results):
    assert isinstance(results, dict), "Test results should be a dictionary."


def test_results_are_has_required_keys(results):
    for key in TEST_RESULTS_REQUIRED_KEYS:
        assert key in results, f"Missing key: {key} in test results."


def test_results_timestamps_are_all_different(results):
    timestamps = results["timestamps"].cpu()
    assert np.all(np.diff(np.sort(timestamps)) > 0)


def test_results_timestamps_differences_are_constant(results):
    timestamps = results["timestamps"].cpu()
    diffs = np.diff(timestamps)
    assert np.all(diffs == diffs[0]), "Timestamps differences are not constant."


def test_prediction_are_numpy_arrays(plotting_data):
    for v in plotting_data.values():
        assert isinstance(v, np.ndarray)


def test_first_and_second_prediction_steps_are_not_equal(plotting_data):
    assert not np.array_equal(
        plotting_data["preds"][:, 0], plotting_data["preds"][:, 1]
    ), "First and second predictions should not be equal."


def test_first_and_second_target_temperatures_are_not_equal(plotting_data):
    assert not np.array_equal(
        plotting_data["target_temps"][:, 0],
        plotting_data["target_temps"][:, 1],
    ), "First and second target temperatures should not be equal."


def test_plotting_data_shapes(plotting_data):
    n_rooms = NUM_ROOMS
    steps = HORIZON + 1  # +1 to include the initial state
    plotting_horizon = steps

    # check they contain the right number of timesteps
    assert (plotting_data["preds"]).shape[1] == plotting_horizon
    assert (plotting_data["target_temps"]).shape[1] == plotting_horizon
    assert (plotting_data["ambient_temps"]).shape[0] == plotting_horizon
    assert (plotting_data["heat_inputs"]).shape[1] == plotting_horizon
    assert len(plotting_data["timestamps"]) == plotting_horizon

    # check they contain the right number of rooms
    assert (plotting_data["preds"]).shape[0] == n_rooms
    assert (plotting_data["target_temps"]).shape[0] == n_rooms
    assert (plotting_data["heat_inputs"]).shape[0] == n_rooms
