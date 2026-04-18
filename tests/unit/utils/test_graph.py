import numpy as np
import pytest

from models.modules.utils import init_physically_consistent_BRCM_adjacency_matrix
from utils.graph import expand_adjacency_matrix


@pytest.mark.parametrize(
    "A, K, expected_size",
    [
        # Single node, no edges
        (np.array([[1]]), 1, 1),
        # Two disconnected nodes
        (np.array([[1, 0], [0, 1]]), 1, 2),
        # Two connected nodes
        (np.array([[1, 1], [1, 1]]), 1, 3),
        # Two connected nodes with K=2
        (np.array([[1, 1], [1, 1]]), 2, 4),
        # Three nodes in a line
        (np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]]), 1, 5),
        # Three nodes in a line with K=2
        (
            np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]]),
            2,
            7,
        ),
        # Fully connected three nodes
        (
            np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]]),
            1,
            6,
        ),
        # Three disconnected nodes with K=3
        (
            np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            3,
            3,
        ),
    ],
)
def test_expand_adjacency_matrix_flexible(A, K, expected_size):
    result = expand_adjacency_matrix(A, K)

    # Check size
    assert result.shape == (expected_size, expected_size)

    # Check all nodes have self-loops
    for i in range(expected_size):
        assert result[i, i] == 1

    # Check symmetry
    assert np.array_equal(result, result.T)

    # Check no direct connections between original nodes
    n = A.shape[0]
    for i in range(n):
        for j in range(n):
            if i != j:
                assert result[i, j] == 0

    # Check each original edge has proper intermediate node
    for i in range(n):
        for j in range(i + 1, n):
            if A[i, j] > 0:
                intermediate_found = False
                for k in range(n, expected_size):
                    if result[i, k] == 1 and result[k, j] == 1:
                        connections = np.where(result[k, :] == 1)[0]
                        connections = connections[connections != k]
                        if set(connections) == {i, j}:
                            intermediate_found = True
                            break
                assert intermediate_found


def test_expand_fully_connected_2x2_adjacency_matrix_by_1():
    K = 1
    A = np.ones((2, 2))
    actual_augmented_A = expand_adjacency_matrix(A, K)
    expected_augmented_A = np.array([[1, 0, 1], [0, 1, 1], [1, 1, 1]])
    assert np.array_equal(expected_augmented_A, actual_augmented_A)


def test_expand_in_line_3x3_adjacency_matrix_by_1():
    K = 1
    A = np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]])
    actual_augmented_A = expand_adjacency_matrix(A, K)
    expected_augmented_A = np.array(
        [
            [1, 0, 0, 1, 0],
            [0, 1, 0, 1, 1],
            [0, 0, 1, 0, 1],
            [1, 1, 0, 1, 0],
            [0, 1, 1, 0, 1],
        ]
    )
    assert np.array_equal(expected_augmented_A, actual_augmented_A)


def test_expand_fully_connected_3x3_adjacency_matrix_by_1():
    K = 1
    A = np.ones((3, 3))
    actual_augmented_A = expand_adjacency_matrix(A, K)
    expected_augmented_A = np.array(
        [
            [1, 0, 0, 1, 1, 0],
            [0, 1, 0, 1, 1, 1],
            [0, 0, 1, 0, 0, 1],
            [1, 1, 0, 1, 0, 0],
            [1, 1, 0, 0, 1, 0],
            [0, 1, 1, 0, 0, 1],
        ]
    )
    assert np.array_equal(expected_augmented_A, actual_augmented_A)


def test_expand_brcm_5_room_building_by_1_interior_walls_only():
    adjacency_matrix = init_physically_consistent_BRCM_adjacency_matrix(
        num_zones=5
    ).numpy()
    K = 1
    actual_augmented_A = expand_adjacency_matrix(adjacency_matrix, K)
    # expects a 11x11 matrix
    upper_left = np.eye(5)
    lower_right = np.eye(6)
    lower_left = np.array(
        [
            [1, 1, 0, 0, 0],
            [1, 0, 1, 0, 0],
            [0, 1, 1, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 1, 0, 1],
            [0, 0, 0, 1, 1],
        ]
    )
    upper_right = lower_left.T
    expected_augmented_A = np.block(
        [[upper_left, upper_right], [lower_left, lower_right]]
    )
    assert np.array_equal(expected_augmented_A, actual_augmented_A)


def test_expand_brcm_5_room_building_by_1_with_interior_and_exterior_walls():
    adjacency_matrix = init_physically_consistent_BRCM_adjacency_matrix(
        num_zones=5
    ).numpy()
    K = 1
    actual_augmented_A = expand_adjacency_matrix(adjacency_matrix, K)
    # expects a 11x11 matrix
    upper_left = np.eye(5)
    lower_right = np.eye(6)
    lower_left = np.array(
        [
            [1, 1, 0, 0, 0],
            [1, 0, 1, 0, 0],
            [0, 1, 1, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 1, 0, 1],
            [0, 0, 0, 1, 1],
        ]
    )
    upper_right = lower_left.T
    expected_augmented_A = np.block(
        [[upper_left, upper_right], [lower_left, lower_right]]
    )
    assert np.array_equal(expected_augmented_A, actual_augmented_A)
