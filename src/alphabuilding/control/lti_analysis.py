import numpy as np


def compute_continuous_tau_max(A: np.ndarray) -> float:
    """
    Computes the dominant time constant (tau_max) for a continuous-time LTI system
    defined by the state matrix A, such that the system remains stable.

    Parameters:
    A (list of list of floats): The state matrix of the LTI system.

    Returns:
    float: The maximum allowable time delay (tau_max) for stability.
    """
    eigenvalues = np.linalg.eigvals(A)
    max_real_part = max(eigenvalues, key=lambda x: x.real).real

    # If the largest real part is non-negative, the system is not stable
    if max_real_part >= 0:
        return 0.0

    tau_max = -1 / max_real_part

    return tau_max


def compute_discrete_tau_max(A: np.ndarray, dt: float) -> float:
    """
    Computes the dominant time constant (tau_max) for a discrete-time LTI system
    defined by the state matrix A, such that the system remains stable.

    Parameters:
    A (list of list of floats): The state matrix of the LTI system.
    dt (float): The time step for the discrete-time system.

    Returns:
    float: The maximum allowable time delay (tau_max) for stability.
    """
    eigenvalues = np.linalg.eigvals(A)
    max_lambda = max(eigenvalues, key=lambda x: abs(x))

    # If the largest real part is non-negative, the system is not stable
    if abs(max_lambda) >= 1:
        return 0.0

    tau_max = -dt / np.log(abs(max_lambda))

    return tau_max


def compute_settling_time(A: np.ndarray, dt: float = 0, tol=2) -> float:
    """Computes the settling time for a continuous-time or discrete-time LTI system defined by the state matrix A.
    a discrete-time system is assumed if dt > 0, and a continuous-time system is assumed if dt = 0.
    The settling time is computed based on the maximum allowable time delay (tau_max) for stability, and the tolerance level (tol) for the system's response.
    Units are the same as the time step (dt) for discrete-time systems, and seconds for continuous-time systems.


    Args:
        A (np.ndarray): The state matrix of the LTI system.
        dt (float, optional): The time step (in any units) for discrete-time systems. Defaults to 0 (continuous-time).
        tol (float, optional): The tolerance level for settling time calculation. Defaults to 2.

    Returns:
        float: The settling time for the system.
    """

    assert dt >= 0, "Time step (dt) must be non-negative"

    tol_percent = tol / 100  # Convert percentage to fraction

    if dt == 0:
        tau_max = compute_continuous_tau_max(A)
        t = -np.log(tol_percent) * tau_max
    else:
        tau_max = compute_discrete_tau_max(A, dt)
        t = -np.log(tol_percent) * tau_max

    assert t >= 0, "Settling time must be non-negative"
    return t
