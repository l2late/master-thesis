from alphabuilding.constants import Levels
from alphabuilding.control.results import ControllerSimulationComparator
from tests.fixtures.factories import (
    concat_simulation_results,
    make_simulation_result,
)


def test_pareto_front_data_has_as_many_experiments_as_mpc_results():
    simulation_resuts = {
        "experiment_1": make_simulation_result(10, "30s"),
        "experiment_2": make_simulation_result(10, "30s"),
    }
    mpc_results = concat_simulation_results(simulation_resuts)

    control_sim_comparator = ControllerSimulationComparator(
        mpc_results=mpc_results,
        reference_results=None,
    )

    pareto_results = control_sim_comparator.pareto_data

    unique_pareto_experiments = pareto_results.index.get_level_values(
        Levels.experiment
    ).nunique()

    assert (
        unique_pareto_experiments
        == mpc_results.index.get_level_values(Levels.experiment).nunique()
        == 2
    )


def test_select_most_energy_efficient_mpc():
    sim_results = {
        "mpc 1": make_simulation_result(10, "30s", u_value=5),
        "mpc 2": make_simulation_result(10, "30s", u_value=10),
        "mpc 3": make_simulation_result(10, "30s", u_value=1),
    }
    mpc_results = concat_simulation_results(sim_results)
    comparator = ControllerSimulationComparator(mpc_results)
    best_model = comparator.select_most_energy_efficient_mpc()
    assert best_model == "mpc 3"


def test_select_least_energy_efficient_mpc():
    sim_results = {
        "mpc 1": make_simulation_result(10, "30s", u_value=5),
        "mpc 2": make_simulation_result(10, "30s", u_value=10),
        "mpc 3": make_simulation_result(10, "30s", u_value=1),
    }
    mpc_results = concat_simulation_results(sim_results)
    comparator = ControllerSimulationComparator(mpc_results)
    best_model = comparator.select_least_energy_efficient_mpc()
    assert best_model == "mpc 2"


def test_select_least_comfortable_mpc():
    sim_results = {
        "mpc 1": make_simulation_result(10, "30s", y_value=50),
        "mpc 2": make_simulation_result(10, "30s", y_value=22),
        "mpc 3": make_simulation_result(10, "30s", y_value=23),
    }
    mpc_results = concat_simulation_results(sim_results)
    comparator = ControllerSimulationComparator(mpc_results)
    worst_model = comparator.select_least_comfortable_mpc()
    assert worst_model == "mpc 1"


def test_select_most_comfortable_mpc():
    sim_results = {
        "mpc 1": make_simulation_result(10, "30s", y_value=50),
        "mpc 2": make_simulation_result(10, "30s", y_value=22),
        "mpc 3": make_simulation_result(10, "30s", y_value=19),
    }
    mpc_results = concat_simulation_results(sim_results)
    comparator = ControllerSimulationComparator(mpc_results)
    best_model = comparator.select_most_comfortable_mpc()
    assert best_model == "mpc 2"
