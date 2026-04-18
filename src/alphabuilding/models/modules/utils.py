import torch
import torch.nn as nn


def initialize_orthogonal_stable_square_matrix(num_states, epsilon=0.1, scale=1.0):
    """Initializes a stable A using an orthogonal matrix."""
    Q = nn.init.orthogonal_(torch.empty(num_states, num_states))
    I = torch.eye(num_states)
    # Start with an energy-preserving transformation and add uniform damping
    A = Q - (1 + epsilon) * I
    return A * scale


def initialize_stable_square_matrix_from_skew_symmetric(
    num_states, epsilon=0.1, scale=1.0
):
    """Initializes a stable A using a skew-symmetric matrix."""
    W = torch.randn(num_states, num_states)
    S = 0.5 * (W - W.t())  # Skew-symmetric part
    I = torch.eye(num_states)
    A = S - epsilon * I  # Guarantees eigenvalues have real part -epsilon
    return A * scale


def initialize_negative_definite_diagonal_square_matrix(
    num_states, min_eigenvalue=-2.0, max_eigenvalue=-0.1, scale=1.0
):
    """Initializes a negative definite diagonal square matrix."""
    diagonal_values = torch.empty(num_states).uniform_(min_eigenvalue, max_eigenvalue)
    A = torch.diag(diagonal_values)
    return A * scale


def initialize_random_square_matrix(num_states, scale=0.1):
    """Initializes a random square matrix without stability guarantees."""
    A = torch.randn(num_states, num_states)
    return A * scale


def initialize_gershgorin_stable_square_matrix(num_states, epsilon=0.1, scale=1.0):
    """Initializes a stable A using the Gershgorin Circle Theorem."""
    off_diagonal_A = torch.randn(num_states, num_states)
    off_diagonal_A.fill_diagonal_(0)  # Zero out the diagonal
    # Calculate the desired diagonal values for stability: make them negative and dominant
    row_sums = torch.sum(torch.abs(off_diagonal_A), dim=1)
    diagonal_values = -row_sums - epsilon
    # Add a diagonal matrix created from `diagonal_values` to the off-diagonal part.
    initial_A = off_diagonal_A + torch.diag(diagonal_values)
    # Verify the properties
    A_eigvals = torch.linalg.eigvals(initial_A)
    assert torch.max(torch.real(A_eigvals)) < 0, (
        "A matrix must have negative real eigenvalues"
    )
    return initial_A * scale  # Scale factor for the matrix


def initialize_symmetric_stable_square_matrix(num_states, epsilon=0.1, scale=1.0):
    """Initializes a symmetric stable A matrix by ensuring all eigenvalues are negative."""
    # Generate a random symmetric matrix
    A = torch.randn(num_states, num_states)
    A = (A + A.T) / 2.0  # Symmetrize

    # Compute eigendecomposition
    eigvals, eigvecs = torch.linalg.eigh(A)

    # Set all eigenvalues to negative values: -|original| - epsilon
    new_eigvals = -torch.abs(eigvals) - epsilon

    # Reconstruct the matrix with new eigenvalues
    A_stable = eigvecs @ torch.diag(new_eigvals) @ eigvecs.T

    return A_stable * scale


def init_physically_consistent_BRCM_adjacency_matrix(
    num_zones: int, scale: float = 1.0
):
    assert num_zones == 5, "This function is specifically for a 5-state system."
    A_matrix = torch.tensor(
        [
            [1, 1, 1, 0, 0],  # Room 1 connects to Rooms 2 and 3, and itself
            [1, 1, 1, 0, 0],  # Room 2 connects to Rooms 1 and 3, and itself
            [1, 1, 1, 1, 1],  # Room 3 connects to Rooms 1, 2, 4, 5, and itself
            [0, 0, 1, 1, 1],  # Room 4 connects to Rooms 3 and 5, and itself
            [0, 0, 1, 1, 1],  # Room 5 connects to Rooms 3 and 4, and itself
        ]
    )
    return A_matrix * scale


def expanded_physically_consistent_BRCM_adjacency_matrix():
    n_rooms = 5
    n_internal_walls = 6  # thermal masses
    n_external_walls = 5  # disturbances
    block_11 = torch.zeros((n_rooms, n_rooms))
    block_12 = torch.tensor(
        [
            [1, 1, 0, 0, 0, 0],
            [1, 0, 1, 0, 0, 0],
            [0, 1, 1, 1, 1, 0],
            [0, 0, 0, 1, 0, 1],
            [0, 0, 0, 0, 1, 1],
        ]
    )
    assert torch.all(
        block_12.sum(dim=1).min() >= 2
    )  # each room connects to at least 2 thermal masses (internal walls)
    assert torch.all(
        block_12.sum(dim=1).max() <= 4
    )  # each room connects to at most 4 thermal masses (internal walls)
    assert (
        block_12.shape[0] == n_rooms and block_12.shape[1] == n_internal_walls
    )  # each thermal mass connects to two rooms
    block_13 = torch.eye(n_external_walls)

    block_21 = block_12.t()
    block_22 = torch.zeros((n_internal_walls, n_internal_walls))
    block_23 = torch.zeros((n_internal_walls, n_external_walls))
    block_31 = block_13.t()
    block_32 = block_23.t()
    block_33 = torch.zeros((n_external_walls, n_external_walls))
    top = torch.cat((block_11, block_12, block_13), dim=1)
    middle = torch.cat((block_21, block_22, block_23), dim=1)
    bottom = torch.cat((block_31, block_32, block_33), dim=1)
    A_expanded = torch.cat((top, middle, bottom), dim=0)

    assert A_expanded.shape[0] == A_expanded.shape[1], (
        "Expanded Adjacency matrix must be square."
    )

    assert A_expanded.shape[0] == n_rooms + 6 + 5, (
        "Expanded Adjacency matrix size does not match expected size."
    )

    return A_expanded


def init_physically_consistent_BRCM_input_matrix(
    num_states: int, num_inputs: int, num_disturbances: int, scale: float = 1.0
):
    """Initializes a B matrix mask consistent with the physical structure of the 5 room BRCM building."""
    assert num_inputs == 5 and num_disturbances == 2, (
        "This function is specifically for a 5-input system, 2 disturbance system"
    )
    if num_states == 5:
        B_matrix = torch.cat((torch.eye(5), torch.ones(5, 2)), dim=1)  # shape (5, 7)
    elif num_states > 5:
        # heat input only affects room states
        # ambient temp and solar radiation disturbances affect all states (rooms and thermal masses)
        upper_B = torch.cat((torch.eye(5), torch.ones(5, 2)), dim=1)  # shape (5, 7)
        lower_B = torch.cat(
            (torch.zeros(num_states - 5, 5), torch.ones(num_states - 5, 2)), dim=1
        )  # shape (num_states-5, 7)
        B_matrix = torch.cat((upper_B, lower_B), dim=0)  # shape (num_states, 7)
    else:
        raise ValueError("num_states must be at least 5.")
    return B_matrix * scale


def initialize_diagonal_B_matrix(
    num_states: int, num_inputs: int, scale: float = 1.0
) -> torch.Tensor:
    """Initializes a diagonal B matrix."""
    if num_states != num_inputs:
        raise ValueError("For diagonal B matrix, num_states must equal num_inputs.")
    return torch.eye(num_states, num_inputs) * scale


def create_stable_square_matrix(num_states: int, device="cuda") -> torch.Tensor:
    """Creates a random matrix A with guaranteed negative real eigenvalues."""
    # Start with a random matrix for off-diagonal elements
    A = torch.randn(num_states, num_states, device=device)

    # Zero out the diagonal to separate it from off-diagonal calculations
    A.fill_diagonal_(0)

    # Calculate the sum of absolute values of off-diagonal elements for each row
    row_sums = torch.sum(torch.abs(A), dim=1)

    # Set the diagonal elements to be negative and dominant
    # A small margin ensures they are strictly negative
    margin = 0.001
    diagonal_A = -row_sums - margin
    A.diagonal().copy_(diagonal_A)

    return A
