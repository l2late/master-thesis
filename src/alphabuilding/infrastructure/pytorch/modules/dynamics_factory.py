import torch
from omegaconf import DictConfig

from alphabuilding.domain.types import GraphTopology
from alphabuilding.infrastructure.pytorch.modules.baseline_dynamics import (
    BuildingDynamics,
    PositiveMaskedBMatrix,
    SystemMatrices,
)
from alphabuilding.infrastructure.pytorch.modules.utils import (
    create_topology_mask,
)
from alphabuilding.models.modules.utils import (
    init_physically_consistent_BRCM_adjacency_matrix,
)


def make_building_dynamics(
    cfg: DictConfig,
    num_zones: int,
    num_latent_states: int,
    topology: GraphTopology,
) -> BuildingDynamics:

    if topology == GraphTopology.UNCONSTRAINED:
        base_adjacency = torch.ones(num_zones, num_zones)
    else:
        base_adjacency = init_physically_consistent_BRCM_adjacency_matrix(
            num_zones=num_zones
        )

    mask = create_topology_mask(
        num_zones=num_zones,
        num_latent_states=num_latent_states,
        topology=topology,
        base_adjacency=base_adjacency,
    )

    num_states = num_zones + num_latent_states

    # Hydra instantiates the A_module with the mask injected here
    # create the correct A matrix based on the topology mask and number of states.
    # A_module = instantiate(cfg.A_module, n=num_states, mask=mask)
    A_module = cfg.A_module(n=num_states, mask=mask)

    B_module = PositiveMaskedBMatrix(
        num_states=num_states,
        num_inputs=cfg.num_inputs,
        num_disturbances=cfg.num_disturbances,
        initializer=cfg.B_initializer,
        scale=cfg.B_scale,
    )

    system_matrices = SystemMatrices(A_module, B_module)
    return BuildingDynamics(system_matrices, num_zones=num_zones, num_states=num_states)
