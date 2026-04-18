import torch

from models.modules.utils import (
    init_physically_consistent_BRCM_input_matrix,
    initialize_physically_consistent_adjacency_matrix,
)


def test_initialize_physically_consistent_adjacency_matrix():
    scale = 0.1
    actual_A_matrix = initialize_physically_consistent_adjacency_matrix(
        num_states=5, scale=scale
    )
    expected_A_matrix = torch.tensor(
        [
            [0.1, 0.1, 0.1, 0, 0],
            [0.1, 0.1, 0.1, 0, 0],
            [0.1, 0.1, 0.1, 0.1, 0.1],
            [0, 0, 0.1, 0.1, 0.1],
            [0, 0, 0.1, 0.1, 0.1],
        ]
    )
    assert torch.allclose(actual_A_matrix, expected_A_matrix), (
        "A matrix does not match expected values"
    )


def test_initialize_physically_consistent_input_matrix():
    scale = 0.1
    actual_B_matrix = init_physically_consistent_BRCM_input_matrix(
        num_states=5, num_inputs=5, num_disturbances=1, scale=scale
    )
    expected_B_matrix = torch.tensor(
        [
            [0.1, 0, 0, 0, 0, 0.1],
            [0, 0.1, 0, 0, 0, 0.1],
            [0, 0, 0.1, 0, 0, 0.1],
            [0, 0, 0, 0.1, 0, 0.1],
            [0, 0, 0, 0, 0.1, 0.1],
        ]
    )
    assert torch.allclose(actual_B_matrix, expected_B_matrix), (
        "B matrix does not match expected values"
    )
