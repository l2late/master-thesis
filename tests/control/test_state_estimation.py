from typing import NamedTuple

import numpy as np
import pytest

from alphabuilding.control.state_estimation import FilteringLuenbergerObserver


class ObserverSystem(NamedTuple):
    observer: FilteringLuenbergerObserver
    A: np.ndarray
    B: np.ndarray
    C: np.ndarray
    L: np.ndarray
    x0: np.ndarray


# FIX: need to make sure the system is stable (eigenvalues of A inside unit circle) and that the observer is stable (eigenvalues of A-LC inside unit circle)
# but this is different for a continuous vs discrete system, so we need to be careful about how we generate the matrices.
@pytest.fixture
def linear_system_2d():
    """Returns a standard 2-state, 2-output system."""
    A = np.array([[-1, 0], [0, -1]])
    B = np.array([[1], [1]])
    C = np.eye(2)
    L = np.eye(2) * 0.5
    x0 = np.array([20.0, 22.0])

    observer = FilteringLuenbergerObserver(A=A, B=B, C=C, L=L, x0=x0)

    return ObserverSystem(observer, A, B, C, L, x0)


# def test_linear_system_2d_fixture(linear_system_2d):
#     sys = linear_system_2d
#     assert sys.A.shape == (2, 2)
#     assert sys.B.shape == (2, 1)
#     assert sys.C.shape == (2, 2)
#     assert sys.L.shape == (2, 2)
#     assert sys.x0.shape == (2,)
#     from numpy.linalg import eigvals
#
#     system_eigs = eigvals(sys.A)
#     np.testing.assert_array_less(
#         np.abs(system_eigs),
#         1,
#         err_msg="System is not stable (eigenvalues must be inside unit circle)",
#     )
#
#     observer_eigs = eigvals(sys.A - sys.L @ sys.C)
#     np.testing.assert_array_less(
#         np.abs(observer_eigs),
#         1,
#         err_msg="Observer is not stable (eigenvalues must be inside unit circle)",
#     )


def test_initialization(linear_system_2d):
    # Unpack the fixture data
    sys = linear_system_2d
    np.testing.assert_allclose(sys.observer.x_hat, sys.x0)


def test_reset(linear_system_2d):
    sys = linear_system_2d

    # Move state away from initial
    sys.observer.update(u_prev=np.array([1.0]), y_current=np.array([21.0, 23.0]))

    # Reset and Verify
    sys.observer.reset(x0=sys.x0)
    np.testing.assert_allclose(sys.observer.x_hat, sys.x0)


@pytest.mark.parametrize(
    "u_val, y_vals",
    [
        (np.array([1.0]), np.array([21.0, 23.0])),  # Standard case
        (np.array([0.0]), np.array([0.0, 0.0])),  # Zero input/output
        (np.array([-5.0]), np.array([10.0, 10.0])),  # Negative control action
    ],
)
def test_update_step_logic(linear_system_2d, u_val, y_vals):
    sys = linear_system_2d

    # Calculate expected strictly using matrix math (The "Oracle")
    # This ensures the test is valid regardless of the inputs provided
    expected_next = sys.A @ sys.x0 + sys.B @ u_val + sys.L @ (y_vals - sys.C @ sys.x0)

    estimate = sys.observer.update(u_prev=u_val, y_current=y_vals)

    np.testing.assert_allclose(estimate, expected_next)


# Helper to generate random consistent systems
def make_system_matrices(n_states, n_inputs, n_outputs):
    rng = np.random.default_rng(42)
    return (
        rng.random((n_states, n_states)),  # A
        rng.random((n_states, n_inputs)),  # B
        rng.random((n_outputs, n_states)),  # C
        rng.random((n_states, n_outputs)),  # L (random but scaled down)
        rng.random(n_states) * 20,  # x0
    )


@pytest.fixture(
    params=[
        (2, 1, 2),  # Case 1: 2 states, 1 input, 2 outputs (MIMO)
        (3, 2, 3),  # Case 2: 3 states, 2 inputs, 3 outputs (MIMO)
        (4, 1, 1),  # Case 3: 4 states, 1 input, 1 output (SISO-ish)
    ],
    ids=["2D-MIMO", "3D-MIMO", "4D-SISO"],
)
def varied_system(request):
    """
    This fixture will cause any test using it to run 3 times.
    """
    n_x, n_u, n_y = request.param
    A, B, C, L, x0 = make_system_matrices(n_x, n_u, n_y)

    observer = FilteringLuenbergerObserver(A=A, B=B, C=C, L=L, x0=x0)

    # Attach dimensions so tests know what shape of input to generate
    return ObserverSystem(observer, A, B, C, L, x0), n_u, n_y


def test_generic_update_properties(varied_system):
    # Unpack the parametrized fixture
    # sys contains the matrices for THIS specific run (e.g., 2D, then 3D...)
    sys, n_u, n_y = varied_system

    # Generate valid inputs for this specific system dimension
    u_test = np.ones(n_u)
    y_test = np.ones(n_y) * 20

    # Run update
    new_state = sys.observer.update(u_prev=u_test, y_current=y_test)

    # Assert shape is correct (generic property)
    assert new_state.shape == sys.x0.shape

    # Assert math is correct (specific logic)
    expected = sys.A @ sys.x0 + sys.B @ u_test + sys.L @ (y_test - sys.C @ sys.x0)
    np.testing.assert_allclose(new_state, expected)


# def test_observer_error_converges_to_zero(linear_system_2d):
#     """
#     Verify that the estimation error decreases over time.
#     This tests the *control theory* logic, not just the arithmetic.
#     """
#     sys = linear_system_2d
#     n_u = sys.B.shape[1]  # Number of inputs from B matrix
#     n_y = sys.C.shape[0]  # Number of outputs from C matrix
#
#     # 1. Simulate a "Real" System (Truth)
#     # We step the real system forward 50 steps
#     true_states = []
#     x_true = sys.x0.copy() + np.array(
#         [5.0, -5.0]
#     )  # Start real system offset from estimate
#
#     # Inputs (Step input)
#     u_seq = [np.ones(n_u) for _ in range(50)]
#
#     errors = []
#
#     for u_k in u_seq:
#         # Simulate Plant
#         # y = Cx (assume no noise for perfect convergence check)
#         y_k = sys.C @ x_true
#
#         # Update Observer
#         x_hat = sys.observer.update(u_prev=u_k, y_current=y_k)
#
#         # Record Error Norm
#         e_norm = np.linalg.norm(x_hat - x_true)
#         errors.append(e_norm)
#
#         # Step Truth Forward
#         x_true = sys.A @ x_true + sys.B @ u_k
#
#     # ASSERTIONS
#
#     # 1. Error should decrease (monotonically-ish, depending on eigenvalues)
#     # Check if final error is significantly smaller than initial error
#     assert errors[-1] < errors[0] * 0.1
#
#     # 2. Final error should be effectively zero (within tolerance)
#     assert errors[-1] < 1e-5


def test_observer_tracking_perfect_model_match(linear_system_2d):
    """
    If the estimate matches the true state perfectly,
    the observer should evolve exactly like the open-loop system.
    """
    sys = linear_system_2d
    n_u = sys.B.shape[1]  # Number of inputs from B matrix
    # n_y = sys.C.shape[0]  # Number of outputs from C matrix

    # Force observer to perfectly match an arbitrary state
    perfect_state = np.array([10.0, 10.0])
    sys.observer.reset(x0=perfect_state)

    u = np.ones(n_u)
    # If y matches Cx exactly...
    y_perfect = sys.C @ perfect_state

    x_next = sys.observer.update(u_prev=u, y_current=y_perfect)

    # ...then the correction term (L * error) should be zero.
    # The observer should behave exactly like A*x + B*u
    expected_open_loop = sys.A @ perfect_state + sys.B @ u

    np.testing.assert_allclose(x_next, expected_open_loop)
