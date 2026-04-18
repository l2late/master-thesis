import numpy as np
import torch


def validate_adjacency_matrix(adjacency_matrix: torch.Tensor, num_states: int):
    assert adjacency_matrix.shape == (
        num_states,
        num_states,
    ), "Adjacency matrix shape must match number of states."
    assert torch.all(adjacency_matrix >= 0), (
        "Adjacency matrix must have non-negative entries because resistances cannot be negative."
    )
    assert torch.all(adjacency_matrix == adjacency_matrix.t()), (
        "Adjacency matrix must be symmetric."
    )
    if torch.all(torch.diag(adjacency_matrix) != 0):
        adjacency_matrix.fill_diagonal_(0)
    return adjacency_matrix


def expand_adjacency_matrix(A: np.ndarray, K):
    """
    Expand a symmetric adjacency matrix by adding K intermediate nodes between each original pair of connected nodes.
    New nodes are appended to the end, and all new connections are undirected.
    The input matrix A should be square and symmetric, with self-loops.
    This function is used to model thermal masses in a building's thermal network.

    Args:
        A: numpy.ndarray, shape (n, n), original adjacency matrix.
        K: int, number of inserted nodes between each original connection.
           Only implemented for K=1 (as per your tests).

    Returns:
        numpy.ndarray, the expanded adjacency matrix of shape (n + m, n + m)
        where m = K * (number of unique edges above the diagonal).
    """
    n = A.shape[0]
    # Find unique undirected edges, excluding self connections
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if A[i, j]:
                edges.append((i, j))

    m = len(edges) * K  # total number of new nodes
    N = n + m  # total size of augmented matrix

    A_aug = np.zeros((N, N), dtype=int)
    # Copy self-loops for original nodes
    for i in range(n):
        A_aug[i, i] = 1

    # Copy self-loops for new nodes
    for i in range(n, N):
        A_aug[i, i] = 1

    # Map each edge to its new intermediate nodes
    new_node_idx = n
    for i, j in edges:
        last = i
        for _ in range(K):
            # Connect last node to the new intermediate node
            A_aug[last, new_node_idx] = 1
            A_aug[new_node_idx, last] = 1
            last = new_node_idx
            new_node_idx += 1
        # Connect the last inserted node to j
        A_aug[last, j] = 1
        A_aug[j, last] = 1

    # Assert it has self-loops
    for i in range(N):
        assert A_aug[i, i] == 1, "All nodes must have self-loops"

    is_symmetric = np.all(A_aug == A_aug.T)
    assert is_symmetric, "The augmented adjacency matrix must be symmetric"
    assert validate_thermal_expansion_simple(A, A_aug, K)[0], (
        validate_thermal_expansion_simple(A, A_aug, K)[1]
    )
    return A_aug


def validate_thermal_expansion_simple(original, augmented, K=1):
    """Expanded Graph validation function
    Performs validation using insights into the block structure of the expanded adjacency matrix."""

    if not isinstance(original, np.ndarray):
        original = original.numpy()

    n = original.shape[0]
    total = augmented.shape[0]
    m = total - n

    # why 2? we assume that each thermal mass connects exactly two original nodes
    num_original_nodes_per_thermal_mass = 2

    # Extract blocks
    I_upper_left = augmented[:n, :n]
    B_upper_right = augmented[:n, n:]
    B_T_lower_left = augmented[n:, :n]
    I_lower_right = augmented[n:, n:]

    # Five essential checks
    checks = [
        (np.array_equal(I_upper_left, np.eye(n)), "Upper left diagonal not identity"),
        (np.array_equal(I_lower_right, np.eye(m)), "Lower right diagonal not identity"),
        (
            np.array_equal(B_upper_right, B_T_lower_left.T),
            "Upper right and lower left blocks not transpose symmetric",
        ),
        (
            np.all(B_upper_right.sum(axis=0) == num_original_nodes_per_thermal_mass),
            "Invalid thermal mass connections",
        ),
        # triu_indices gives a [2, E] tensor giving the indices of the upper triangle of the matrix, excluding the diagonal
        (
            m == np.sum(original[np.triu_indices(n, 1)] > 0) * K,
            "Wrong number of thermal masses",
        ),
    ]

    for condition, error in checks:
        if not condition:
            return False, error

    return True, error
