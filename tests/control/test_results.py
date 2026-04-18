import pytest

from alphabuilding.control.results import ControllerSimulationComparator
from tests.fixtures.factories import (
    concat_simulation_results,
    make_simulation_result,
)

valid_simulation_results = {
    "experiment_1": make_simulation_result(10, "30s"),
    "experiment_2": make_simulation_result(10, "30s"),
}
valid_mpc_results = concat_simulation_results(valid_simulation_results)


def test_different_timeindex_lengths_raises_error():
    different_length_simulation_results = {
        "experiment_1": make_simulation_result(10, "30s"),
        "experiment_2": make_simulation_result(11, "30s"),
    }
    mpc_results = concat_simulation_results(different_length_simulation_results)

    reference_results = make_simulation_result(length=10, frequency="30s")
    with pytest.raises(ValueError):
        ControllerSimulationComparator(mpc_results, reference_results)


def test_different_timeindex_frequencies_raises_error():
    different_frequency_simulation_results = {
        "experiment_1": make_simulation_result(10, "30s"),
        "experiment_2": make_simulation_result(11, "30s"),
    }
    mpc_results = concat_simulation_results(different_frequency_simulation_results)
    reference_results = make_simulation_result(length=10, frequency="30s")
    with pytest.raises(ValueError):
        ControllerSimulationComparator(mpc_results, reference_results)


def test_same_timeindices():
    reference_results = make_simulation_result(length=10, frequency="30s")
    ControllerSimulationComparator(valid_mpc_results, reference_results)


def test_different_timeindex_lengths_between_mpc_and_reference_raises():
    reference_results = make_simulation_result(length=20, frequency="30s")
    with pytest.raises(ValueError):
        ControllerSimulationComparator(valid_mpc_results, reference_results)
