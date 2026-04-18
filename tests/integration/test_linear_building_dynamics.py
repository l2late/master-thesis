import torch

from infrastructure.lightning.modules.neural_ode import LinearBuildingDynamics

NUM_STATES = 10
NUM_INPUTS = 5
NUM_DISTURBANCES = 1
BATCH_SIZE = 2


def test_building_dynamics_output_shape():
    x = torch.rand(BATCH_SIZE, NUM_STATES)
    u = torch.rand(BATCH_SIZE, NUM_INPUTS)
    d = torch.rand(BATCH_SIZE, NUM_DISTURBANCES)

    dynamics = LinearBuildingDynamics(
        num_states=NUM_STATES, num_inputs=NUM_INPUTS, num_disturbances=NUM_DISTURBANCES
    )
    dxdt = dynamics.forward(x=x, u=u, d=d)
    assert dxdt.shape == (BATCH_SIZE, NUM_STATES)
