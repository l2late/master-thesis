import numpy as np
import pytest

from alphabuilding.control.brcm_building import (
    BRCMBuildingSimulator,
    BRCMStateSpaceModel,
    TimeDomain,
    read_brcm_ss_mat_file,
)
from alphabuilding.utils.paths import paths


@pytest.fixture(scope="module")
def mat_file_path():
    return paths.data_dir / "building_plant_data.mat"


@pytest.fixture(scope="module")
def ss_model(mat_file_path):
    ss_model = read_brcm_ss_mat_file(mat_file_path)
    return ss_model


@pytest.fixture(scope="module")
def simulator(ss_model):
    simulator = BRCMBuildingSimulator(ss_model, initial_temp=20.0)
    return simulator


@pytest.fixture
def u_sequence():
    return np.array([[0.5], [0.25], [0.0]])


def test_continuous_time_domain_enum_does_not_require_sample_time():
    time_domain_continuous = TimeDomain.CONTINUOUS
    assert time_domain_continuous.requires_sample_time is False


def test_discrete_time_domain_enum_requires_sample_time():
    time_domain_discrete = TimeDomain.DISCRETE
    assert time_domain_discrete.requires_sample_time is True


def test_read_brcm_ss_mat_file(mat_file_path):
    ss = read_brcm_ss_mat_file(mat_file_path)
    assert ss.A.shape[0] == ss.nx
    assert ss.Bu.shape[1] == ss.nu
    assert ss.Bd.shape[1] == ss.nd
    assert ss.nx == 118
    assert ss.nx == 118


def test_reset_simulator_state(simulator):
    initial_temp = 22.0
    state = simulator.reset(initial_temp=initial_temp)
    assert state.shape == (simulator.ss.nx,)
    assert np.all(state == initial_temp)


def test_simulate_one_step(simulator):
    u_radiators = np.ones(5) * 25
    t_amb = 25
    solar_rad = 400
    room_states = simulator.simulate_one_step(u_radiators, t_amb, solar_rad)
    assert room_states.shape == (5,)


def test_simulate_multi_step_with_wrong_input_dim_raises_error(simulator):
    wrong_u_sequence = np.array([[0.5, 0.25], [0.0, 0.1]])
    t_amb = np.ones((2,)) * 20
    solar_rad = np.ones((2,)) * 400
    with pytest.raises(AssertionError):
        _ = simulator.simulate_multi_step(wrong_u_sequence, t_amb, solar_rad)


def test_simulate_multi_step_with_right_shape_inputs(simulator):
    n_steps = 6
    u_radiators = np.ones((n_steps, 5)) * 25
    t_amb = np.ones((n_steps,)) * 20
    solar_rad = np.ones((n_steps,)) * 400
    room_temps_traj = simulator.simulate_multi_step(u_radiators, t_amb, solar_rad)
    assert room_temps_traj.shape == (n_steps + 1, 5)


def test_simulate_multi_step_with_wrong_shape_u_rad(simulator):
    n_steps = 6
    u_radiators = np.ones((n_steps - 1, 5)) * 25
    t_amb = np.ones((n_steps,)) * 20
    solar_rad = np.ones((n_steps,)) * 400
    with pytest.raises(AssertionError):
        _ = simulator.simulate_multi_step(u_radiators, t_amb, solar_rad)


def test_simulate_multi_step_with_wrong_shape_t_amb(simulator):
    n_steps = 6
    u_radiators = np.ones((n_steps, 5)) * 25
    t_amb = np.ones((n_steps - 1,)) * 20
    solar_rad = np.ones((n_steps,)) * 400
    with pytest.raises(AssertionError):
        _ = simulator.simulate_multi_step(u_radiators, t_amb, solar_rad)


def test_simulate_multi_step_with_wrong_shape_solar_rad(simulator):
    n_steps = 6
    u_radiators = np.ones((n_steps, 5)) * 25
    t_amb = np.ones((n_steps,)) * 20
    solar_rad = np.ones((n_steps - 1,)) * 400
    with pytest.raises(AssertionError):
        _ = simulator.simulate_multi_step(u_radiators, t_amb, solar_rad)


def test_simulate_multi_step_updates_internal_state(simulator):
    n_steps = 1
    u_radiators = np.ones((n_steps, 5)) * 25
    t_amb = np.ones((n_steps,)) * 20
    solar_rad = np.ones((n_steps,)) * 400
    initial_state = simulator.x.copy()
    _ = simulator.simulate_multi_step(u_radiators, t_amb, solar_rad)
    assert not np.all(simulator.x == initial_state)


def test_init_from_mat_file(mat_file_path):
    simulator = BRCMBuildingSimulator.from_mat_file(mat_file_path, initial_temp=21.0)
    assert np.all(simulator.x == 21.0)
    assert isinstance(simulator.ss, BRCMStateSpaceModel)


# use the model for cosimulation of the real plant and the mpc internal model
