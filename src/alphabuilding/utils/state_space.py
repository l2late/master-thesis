import numpy as np
import torch
from scipy.signal import cont2discrete


def get_continuous_A_B_C_D_from_dynamics_module(
    dynamics_module: torch.nn.Module,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract system matrices and GRU model from trained module."""
    A = dynamics_module.A_matrix.detach().cpu().numpy()
    B = dynamics_module.B_matrix.detach().cpu().numpy()
    if hasattr(dynamics_module, "state_scale_matrix"):
        S = dynamics_module.state_scale_matrix.detach().cpu().numpy()
        S_inv = dynamics_module.inv_state_scale_matrix.detach().cpu().numpy()
        A = S_inv @ A @ S
        B = S_inv @ B
    n_states = A.shape[0]
    C = np.zeros((5, n_states))
    C[:5, :5] = np.eye(5)
    D = np.zeros((C.shape[0], B.shape[1]))
    return A, B, C, D


def discretize_system(A_cont, B_cont, C, dt_hours) -> tuple[np.ndarray, np.ndarray]:
    """
    Discretize continuous-time state-space system.

    Args:
        A_cont: Continuous A matrix (n_states, n_states)
        B_cont: Continuous B matrix (n_states, n_inputs)
        C: Output matrix (n_outputs, n_states) - unchanged
        dt: Sampling time in hours

    Returns:
        A_d, B_d: Discretized matrices
    """

    # Create dummy D matrix (direct feedthrough, usually zeros)
    D = np.zeros((C.shape[0], B_cont.shape[1]))

    # Discretize using zero-order hold
    system_discrete = cont2discrete(
        (A_cont, B_cont, C, D),
        dt_hours,  # Use appropriate time unit
        method="zoh",
    )

    A_d, B_d, _, _, _ = system_discrete

    return A_d, B_d


def diagnose_continuous_system(Ac, Bc, dt_hours):
    """Check continuous system before discretization"""
    import scipy.linalg

    print("=== Continuous System Diagnostics ===")
    print(f"Ac shape: {Ac.shape}")
    print(f"Bc shape: {Bc.shape}")
    print(f"Timestep dt: {dt_hours} hours")

    # Check eigenvalues
    eigs = scipy.linalg.eigvals(Ac)
    print("\nAc eigenvalues:")
    print(f"  Real parts - min: {eigs.real.min():.2e}, max: {eigs.real.max():.2e}")
    print(f"  Imag parts - min: {eigs.imag.min():.2e}, max: {eigs.imag.max():.2e}")
    print(f"  Largest magnitude: {np.abs(eigs).max():.2e}")

    # Check if unstable
    if np.any(eigs.real > 0):
        print(
            f"  WARNING: {np.sum(eigs.real > 0)} UNSTABLE eigenvalues (positive real part)!"
        )

    # Check condition number
    cond_Ac = np.linalg.cond(Ac)
    print(f"\nCondition number of Ac: {cond_Ac:.2e}")
    if cond_Ac > 1e10:
        print("  WARNING: Ac is severely ill-conditioned!")

    # Check stiffness ratio
    if np.abs(eigs).min() > 0:
        stiffness = np.abs(eigs).max() / np.abs(eigs).min()
        print(f"Stiffness ratio: {stiffness:.2e}")
        if stiffness > 1e6:
            print("  WARNING: System is extremely stiff!")

    # Check matrix norms
    print("\nMatrix norms:")
    print(f"  ||Ac||_2: {np.linalg.norm(Ac, 2):.2e}")
    print(f"  ||Bc||_2: {np.linalg.norm(Bc, 2):.2e}")
