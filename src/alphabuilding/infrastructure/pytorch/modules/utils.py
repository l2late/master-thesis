import torch
import torch.nn as nn
from omegaconf import DictConfig

from alphabuilding.domain.types import GraphTopology
from alphabuilding.models.modules.utils import (
    init_physically_consistent_BRCM_adjacency_matrix,
    init_physically_consistent_BRCM_input_matrix,
    initialize_diagonal_B_matrix,
    initialize_gershgorin_stable_square_matrix,
    initialize_negative_definite_diagonal_square_matrix,
    initialize_orthogonal_stable_square_matrix,
    initialize_random_square_matrix,
)


# FIX: understand what happens here
def inverse_softplus(y: torch.Tensor, eps: float = 1e-9) -> torch.Tensor:
    """
    Compute x such that softplus(x) ≈ y.

    Uses:
        softplus(x) = log(1 + exp(x))
        ⇒ x = log(exp(y) - 1)

    Numerically stable via log1p and a small lower bound eps.
    Assumes y >= 0 on the support where it is used.
    """
    # For small y, exp(y) - 1 ≈ y, so we clamp to avoid log(0) / negatives.
    return torch.log(torch.expm1(y).clamp_min(eps))


class PositiveMasked(nn.Module):
    """
    Constrains parameters to be positive where mask=1 and exactly zero where mask=0.

    forward: raw -> constrained
        Y = softplus(raw).clamp_min(eps) * mask

    right_inverse: constrained -> raw
        raw = inverse_softplus(Y) on mask==1, 0 elsewhere
    """

    def __init__(self, mask: torch.Tensor, eps: float = 1e-9):
        super().__init__()
        # Always store mask as float for clean multiplication; shape is fixed.
        self.register_buffer("mask", mask.float())
        self.eps = eps

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        Y = torch.nn.functional.softplus(X).clamp_min(self.eps)
        return Y * self.mask

    def right_inverse(self, Y: torch.Tensor) -> torch.Tensor:
        # Inverse only on active entries; masked entries are fixed to 0 in raw space
        raw = torch.zeros_like(Y)
        active = self.mask.bool()
        raw[active] = inverse_softplus(Y[active], eps=self.eps)
        return raw

    def extra_repr(self) -> str:
        density = float(self.mask.mean().item())
        return f"sparsity={1.0 - density:.2%}, eps={self.eps}"


A_INITIALIZERS = {
    "orthogonal": initialize_orthogonal_stable_square_matrix,
    "gershgorin": initialize_gershgorin_stable_square_matrix,
    "physical": init_physically_consistent_BRCM_adjacency_matrix,
    "random": initialize_random_square_matrix,
    "diagonal": initialize_negative_definite_diagonal_square_matrix,
}

B_INITIALIZERS = {
    "diagonal": lambda num_states, num_inputs, num_disturbances, scale: (
        initialize_diagonal_B_matrix(num_states, num_inputs, scale)
    ),
    "physical": init_physically_consistent_BRCM_input_matrix,
    "random_positive": lambda num_states, num_inputs, num_disturbances, scale: (
        torch.rand(num_states, num_inputs + num_disturbances) * scale
    ),
}


def create_topology_mask(
    num_zones: int,
    num_latent_states: int,
    topology: GraphTopology,
    base_adjacency: torch.Tensor,
) -> torch.Tensor:
    """
    Create a structured (num_zones + num_latent_states)² mask encoding
    the coupling topology between zones and latent states.

    Blocks:
        ZZ: zones   → zones   [num_zones,          num_zones]
        ZL: zones   → latent  [num_zones,          num_latent_states]
        LZ: latent  → zones   [num_latent_states,  num_zones]
        LL: latent  → latent  [num_latent_states,  num_latent_states]
    """
    assert isinstance(topology, GraphTopology), f"Invalid topology: {topology}"
    assert base_adjacency.shape == (num_zones, num_zones), (
        f"base_adjacency must be ({num_zones}, {num_zones}), "
        f"got {tuple(base_adjacency.shape)}"
    )

    device = base_adjacency.device
    dtype = base_adjacency.dtype

    def ones(shape):
        return torch.ones(shape, device=device, dtype=dtype)

    def eye(n_rows, n_cols=None):
        return torch.eye(
            n_rows,
            n_cols if n_cols is not None else n_rows,
            device=device,
            dtype=dtype,
        )

    if topology == GraphTopology.UNCONSTRAINED:
        mask_ZZ = ones((num_zones, num_zones))
        mask_ZL = ones((num_zones, num_latent_states))
        mask_LZ = ones((num_latent_states, num_zones))
        mask_LL = ones((num_latent_states, num_latent_states))

    elif topology == GraphTopology.PHYSICAL_FULLY_CONNECTED:
        mask_ZZ = base_adjacency.clone().to(dtype)
        mask_ZL = ones((num_zones, num_latent_states))
        mask_LZ = ones((num_latent_states, num_zones))
        mask_LL = ones((num_latent_states, num_latent_states))

    elif topology == GraphTopology.FULLY_CONNECTED_ONE_TO_ONE:
        assert num_latent_states == num_zones, (
            "FULLY_CONNECTED_ONE_TO_ONE requires num_latent_states == num_zones, "
            f"got {num_latent_states} vs {num_zones}"
        )
        mask_ZZ = ones((num_zones, num_zones))  # zones can interact with all zones
        mask_ZL = eye(num_zones, num_latent_states)  # zone -> latent
        mask_LZ = eye(num_latent_states, num_zones)  # latent -> zone
        mask_LL = eye(num_latent_states)  # self only

    elif topology == GraphTopology.PHYSICAL_ONE_TO_ONE:
        assert num_latent_states == num_zones, (
            "PHYSICAL_ONE_TO_ONE requires num_latent_states == num_zones, "
            f"got {num_latent_states} vs {num_zones}"
        )
        mask_ZZ = base_adjacency.clone().to(dtype)
        mask_ZL = eye(num_zones, num_latent_states)  # zone -> latent
        mask_LZ = eye(num_latent_states, num_zones)  # latent -> zone
        mask_LL = eye(num_latent_states)  # self only

    elif topology == GraphTopology.PHYSICAL_ONE_TO_MANY:
        mask_ZZ = base_adjacency.clone().to(dtype)
        mask_ZL = ones((num_zones, num_latent_states))  # zone -> latent
        mask_LZ = ones((num_latent_states, num_zones))  # latent -> zone
        mask_LL = eye(num_latent_states)  # self only

    else:
        raise ValueError(f"Unhandled topology: {topology}")

    # --- Assemble full block matrix ---
    top = torch.cat((mask_ZZ, mask_ZL), dim=1)
    bottom = torch.cat((mask_LZ, mask_LL), dim=1)
    full_mask = torch.cat((top, bottom), dim=0)

    assert full_mask.shape == (
        num_zones + num_latent_states,
        num_zones + num_latent_states,
    )
    return full_mask
