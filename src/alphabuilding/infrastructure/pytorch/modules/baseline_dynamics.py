import math
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.utils.parametrize as parametrize
from torch import Tensor
from torch.nn import functional as F

from alphabuilding.infrastructure.pytorch.modules.utils import (
    B_INITIALIZERS,
    PositiveMasked,
    inverse_softplus,
)


def init_stable_metzler_params(
    off_diag_params: nn.Parameter,
    mask: torch.Tensor,
    margin: float = 1e-3,
) -> torch.Tensor:
    """In-place stable init for any Metzler parametrization."""
    with torch.no_grad():
        off_diag = nn.functional.softplus(off_diag_params) * mask
        off_diag.fill_diagonal_(0.0)
        row_sums = off_diag.sum(dim=1)
        diag_vals = -(row_sums + margin)
    off_diag_params.data.copy_(inverse_softplus(off_diag.clamp_min(1e-9)))
    return diag_vals


class SoftStableMetzlerMatrix(nn.Module):
    """Soft-constrained: initialized stable, free to move, penalty exposed."""

    def __init__(
        self,
        n: int,
        mask: Tensor,
        scale: float = 0.01,
        margin: float = 1e-3,
        tau: float = 2400.0,
    ):
        super().__init__()
        assert tau >= math.log(n) / margin, (
            f"tau={tau} is too small for the desired margin={margin} and matrix size={n}. Cause: The upper bound of the logsumexp approximation of the max(eigenvalues) used for the instability penalty is to large relative to the chosen margin. More precisely, the penalty will be too large before reaching the margin. This will lead to unintended behavior of the optimization. Consider increasing tau to be much larger than log(n)/margin={math.log(n) / margin:.2f} or use a scheduler to increase tau during training as the models eigenvalues approach the margin"
        )
        self.margin = margin
        self.tau = tau
        self.register_buffer("mask", mask)
        self.off_diag_params = nn.Parameter(torch.rand(n, n) * scale)
        diag_vals = init_stable_metzler_params(self.off_diag_params, mask, margin)
        # FREE parameter, but initialized to be stable
        self.diag_strength = nn.Parameter(diag_vals)

    def forward(self) -> Tensor:
        off_diag = F.softplus(self.off_diag_params) * self.mask
        off_diag = off_diag - off_diag * torch.eye(
            off_diag.shape[0], device=off_diag.device
        )
        return off_diag + torch.diag(self.diag_strength)  # diag unconstrained

    def stability_penalty(self) -> Tensor:
        return logsumexp_stability_penalty(
            self.forward(), margin=self.margin, tau=self.tau
        )
        # return sum_real_eigenvalue_penalty(self.forward())


# class GershgorinStableMetzlerMatrix(nn.Module):
#     """Hard-constrained: forward() always returns Hurwitz Metzler."""
#
#     def __init__(self, n: int, mask: Tensor, scale: float = 0.1, margin: float = 1e-3):
#         super().__init__()
#         self.register_buffer("mask", mask)
#         self.off_diag_params = nn.Parameter(torch.rand(n, n) * scale)
#         self.diag_strength = nn.Parameter(torch.zeros(n))
#         # Single shared init — no logic duplication
#         diag_vals = init_stable_metzler_params(self.off_diag_params, mask, margin)
#         self.diag_strength.data.copy_(diag_vals)
#
#     def forward(self) -> Tensor:
#         off_diag = F.softplus(self.off_diag_params) * self.mask
#         eye = torch.eye(off_diag.shape[0], device=off_diag.device, dtype=off_diag.dtype)
#         off_diag = off_diag * (1.0 - eye)
#         row_sums = off_diag.sum(dim=1)
#         # the diagonals are forced to be negative enough to ensure stability via Gershgorin circles,
#         # but the diag_strength parameter allows to adjust how negative they are
#         diag = -(row_sums + F.softplus(self.diag_strength))
#         return off_diag + torch.diag(diag)


@dataclass
class LTIMatrices:
    A: Tensor
    B: Tensor


class SystemMatrices(nn.Module):
    """Owns A and B parametrizations. Single responsibility: produce LTI matrices."""

    def __init__(
        self,
        A_module: nn.Module,  # Any module with forward() -> Tensor
        B_module: nn.Module,  # Any module with forward() -> Tensor
    ):
        super().__init__()
        self.A_module = A_module
        self.B_module = B_module

    def forward(self) -> LTIMatrices:
        return LTIMatrices(A=self.A_module(), B=self.B_module())

    def stability_penalty(self) -> Tensor | None:
        """Delegate to A_module if it supports soft penalty, else None."""
        if hasattr(self.A_module, "stability_penalty"):
            return self.A_module.stability_penalty()
        return None


class PositiveMaskedBMatrix(nn.Module):
    """B matrix with positivity + sparsity constraints via parametrize."""

    def __init__(
        self, num_states, num_inputs, num_disturbances, initializer: str, scale: float
    ):
        super().__init__()
        initial_B = B_INITIALIZERS[initializer](
            num_states, num_inputs, num_disturbances, scale
        )
        assert (initial_B >= 0).all()
        B_mask = (initial_B > 0).float()
        self._raw = nn.Parameter(torch.zeros_like(initial_B))
        # register parametrization "PositiveMasked" that transforms _raw into the actual B matrix with the desired constraints
        parametrize.register_parametrization(self, "_raw", PositiveMasked(B_mask))
        with torch.no_grad():
            self._raw = initial_B  # triggers right_inverse of PositiveMasked to set _raw such that the initial B matrix is exactly initial_B after the parametrization transform
        assert torch.allclose(self._raw, initial_B), (
            "PositiveMasked.right_inverse round-trip failed"
        )

    def forward(self) -> Tensor:
        return self._raw


class BuildingDynamics(nn.Module):
    """
    Computes dx/dt = Ax + B[u; d].
    Does NOT own parametrization decisions — receives SystemMatrices.
    """

    def __init__(
        self, system_matrices: SystemMatrices, num_zones: int, num_states: int
    ):
        super().__init__()
        self.system_matrices = system_matrices
        self.num_zones = num_zones
        self.num_states = num_states
        # Cache is explicit and invalidated by the training loop
        self._cached: LTIMatrices | None = None

    @property
    def A_matrix(self) -> Tensor:
        if self._cached is not None:
            return self._cached.A
        return self.system_matrices.A_module()

    @property
    def B_matrix(self) -> Tensor:
        if self._cached is not None:
            return self._cached.B
        return self.system_matrices.B_module()

    def cache_matrices(self) -> None:
        """Call once per training step. Downstream forward calls use the cache."""
        self._cached = self.system_matrices()

    def invalidate_cache(self) -> None:
        self._cached = None

    def forward(self, x: Tensor, u: Tensor, d: Tensor) -> Tensor:
        mats = self._cached if self._cached is not None else self.system_matrices()
        v = torch.cat((u, d), dim=-1)
        return x @ mats.A.t() + v @ mats.B.t()

    def stability_penalty(self) -> Tensor | None:
        return self.system_matrices.stability_penalty()

    # TODO: make the choice of tau adaptive so it doesn't overpower the margin, and negatively affect the desired gradient behavior. log(n)/tau << margin -> tau >> log(n)/margin where n = A.shape[0] is the number of eigenvalues being approximated in the logsumexp, to ensure that the approximation is tight enough around the margin to provide meaningful gradients for stability improvement.
    # Theoretically, the margin could be determined from the training data: determine the "slowest" modes (closest to 0) and make sure the margin allows for those modes to be stabilized without vanishing gradients (too negative eigenvalues cause gradients to vanish, while positive eigenvalues cause instability and exploding gradients)


def logsumexp_stability_penalty(A, margin: float = 0.0, tau: float = 1.0):
    """Approximate max Re(lambda) with a smooth function: max_real_eig ≈ tau * logsumexp(Re(lambda)/tau)
    This provides a smooth penalty that can be used during training to encourage stability, even when eigenvalues are close to the margin.
    The penalty is zero when max_real_eig < -margin and grows smoothly as max_real_eig approaches and exceeds -margin.

    Args:
        A: System matrix
        margin: Desired stability margin (e.g., -1e-3 means we want max Re(lambda) < -1e-3)
        tau: Smoothness parameter for the approximation (higher tau → closer to true max but less
            smooth gradients) needs to be CHOSEN CAREFULLY based on the scale of eigenvalues,
            to not overpower the margin, and negatively affect the desired gradient behavior.
    """
    eigvals = torch.linalg.eigvals(A)  # shape (n,) complex tensor of eigenvalues
    # Smooth approximation of max(Re(lambda)) using logsumexp
    approx_max_real_eig = torch.logsumexp(eigvals.real * tau, dim=0) / tau
    # add margin to shift the penalty so that it's zero when approx_max_real_eig = -margin
    z = approx_max_real_eig + margin
    # Use softplus to create a smooth approximation of relu that is zero when z < 0 (i.e., approx_max_real_eig < -margin) and grows smoothly when z > 0 (i.e., approx_max_real_eig > -margin), reuse tau to control sharpness of the penalty increase around the margin
    penalty = torch.nn.functional.softplus(z, beta=tau)
    return penalty


def max_real_eigenvalue_penalty(A, margin: float = 0.0):
    """Computes a penalty based on the maximum real part of eigenvalues.
    Penalty is zero when max Re(lambda) < -margin and grows quadratically when max Re(lambda) exceeds -margin.
    Note: this is a non-smooth penalty and may lead to optimization difficulties when eigenvalues are close to the margin, but it directly targets the maximum real eigenvalue.

    Args:
        A: System matrix
        margin: Desired stability margin (e.g., -1e-3 means we want max Re(lambda) < -1e-3)
    """
    eigvals = torch.linalg.eigvals(A)
    max_real_eig = eigvals.real.max()
    violation = torch.nn.functional.relu(max_real_eig + margin)
    penalty = violation**2
    return penalty


def sum_real_eigenvalue_penalty(A):
    """Computes a penalty based on the sum of real part of eigenvalues.
    Penalty is zero when Re(lambda) < 0 and grows quadratically when max Re(lambda) > 0

    Args:
        A: System matrix
        margin: Desired stability margin (e.g., -1e-3 means we want max Re(lambda) < -1e-3)
    """
    eigvals = torch.linalg.eigvals(A)
    sum_real_eig = eigvals.real.sum()
    violation = torch.nn.functional.relu(sum_real_eig)
    penalty = violation**2
    return penalty


def log_barrier_stability_penalty(
    A: torch.Tensor,
    violation_margin: float = 0.0,
    beta: float = 1e-2,
) -> torch.Tensor:
    eigvals = torch.linalg.eigvals(A)
    re_parts = eigvals.real
    # +1e-9 for numerical stability
    penalty = -beta * torch.sum(torch.log(-re_parts + violation_margin))
    return penalty
