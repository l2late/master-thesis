import pytest
import torch

from infrastructure.lightning.modules.neural_ode import (
    InterpolatedODEWrapper,
    LinearBuildingDynamics,
)
from infrastructure.pytorch.interpolation import zoh_interp

BATCH_SIZE = 2
NUM_DISTURBANCES = 1
NUM_STATES = 3
NUM_INPUTS = 4
NUM_TIME_STEPS = 5


@pytest.fixture
def dynamics():
    module = LinearBuildingDynamics(
        num_states=NUM_STATES,
        num_inputs=NUM_INPUTS,
        num_disturbances=NUM_DISTURBANCES,
    )
    return module


# NOTE: Convention across the code is to have [Batch, Timesteps, Channels] to be consistent with the way the Pytorch dataset batches are delivered


@pytest.fixture
def u():
    u = torch.rand(BATCH_SIZE, NUM_TIME_STEPS, NUM_INPUTS)
    return u


@pytest.fixture
def t_eval():
    t_eval = torch.linspace(0, 1, NUM_TIME_STEPS)
    return t_eval


@pytest.fixture
def d():
    d = torch.rand(BATCH_SIZE, NUM_TIME_STEPS, NUM_DISTURBANCES)
    return d


def test_zoh_interp():
    t_span = torch.tensor([0.0, 1.0, 2.0, 3.0])
    u = torch.tensor([[10.0, 18.0, 13.0, 15.0], [20.0, 28.0, 23.0, 25.0]]).unsqueeze(
        -1
    )  # Shape (B=2, T=4, F=1)
    t_test = torch.tensor([0.0, 0.5, 1.5, 2.0, 2.5, 3.0, 3.1])  # Shape (T_test,)
    u_interpolated_expected = torch.tensor(
        [
            [10.0, 10.0, 18.0, 13.0, 13.0, 15.0, 15.0],
            [20.0, 20.0, 28.0, 23.0, 23.0, 25.0, 25.0],
        ]
    ).unsqueeze(-1)  # Shape (B=1, T_test=7, F=1)
    u_interpolated = zoh_interp(t_test, t_span, u)
    assert u_interpolated.shape == (2, len(t_test), 1)  # (B, T_test, F)
    assert torch.equal(u_interpolated, u_interpolated_expected)


def test_instantiation(dynamics, u, t_eval, d):
    ode_func = InterpolatedODEWrapper(
        dynamics,
        u,
        t_eval,
        future_ambient_temp_traj=d,
        interpolation_method="zoh",
    )
    assert isinstance(ode_func, torch.nn.Module)


def test_u_and_t_eval_length_mismatch_raises_value_error(dynamics, t_eval, d):
    u = torch.rand(BATCH_SIZE, NUM_TIME_STEPS + 1, NUM_INPUTS)
    with pytest.raises(ValueError):
        InterpolatedODEWrapper(
            dynamics,
            u,
            t_eval,
            future_ambient_temp_traj=d,
            interpolation_method="zoh",
        )


def test_d_and_t_eval_length_mismatch_raises_value_error(dynamics, u, t_eval):
    d = torch.rand(BATCH_SIZE, NUM_TIME_STEPS + 1, NUM_DISTURBANCES)
    with pytest.raises(ValueError):
        InterpolatedODEWrapper(
            dynamics,
            u,
            t_eval,
            future_ambient_temp_traj=d,
            interpolation_method="zoh",
        )


def test_interpolation_at_t0_succeeds(dynamics, u, t_eval, d):
    ode_func = InterpolatedODEWrapper(
        dynamics,
        u,
        t_eval,
        future_ambient_temp_traj=d,
        interpolation_method="zoh",
    )
    t0 = torch.tensor(0.0)  # scalar tensor as expected by torchdiffeq
    x = torch.rand(BATCH_SIZE, NUM_STATES)
    out = ode_func(t0, x)
    assert out.shape == (BATCH_SIZE, NUM_STATES)  # one dxdt per state per batch
