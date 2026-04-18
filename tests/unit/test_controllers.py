import numpy as np
import pandas as pd
import pytest

from alphabuilding.control.controllers import (
    RbcController,
)
from alphabuilding.utils.paths import paths

N_ROOMS = 5
N_ACTUATORS = N_ROOMS
N_DISTURBANCES = 2
U_MAX = np.ones(N_ROOMS) * 50.0
U_MIN = np.zeros(N_ROOMS)
DEADBAND = np.ones(N_ROOMS) * 0.5

EXPECTED_RBC_TEST_DATA = paths.test_data_dir / "expected_rbc_simulation_results.parquet"


@pytest.fixture
def rbc_controller():
    return RbcController(
        n_actuators=5,
        u_max=U_MAX,
        u_min=U_MIN,
        deadband=DEADBAND,
    )


@pytest.fixture(scope="session")
def expected_rbc_results_df():
    return pd.read_parquet(EXPECTED_RBC_TEST_DATA)


def test_rbc_simulation_results(expected_rbc_results_df):
    assert isinstance(expected_rbc_results_df, pd.DataFrame), (
        "Expected RBC results should be a DataFrame"
    )
    assert not expected_rbc_results_df.empty, (
        "Expected RBC results DataFrame should not be empty"
    )


def test_get_rbc_controller_heats_when_all_rooms_too_cold(rbc_controller):
    T_setpoint = np.ones(N_ROOMS) * 22.0

    # Test case: all rooms below setpoint - deadband -> all heaters ON
    T_meas = T_setpoint - DEADBAND - 1.0
    u = rbc_controller.get_action(current_state=T_meas, reference=T_setpoint)
    np.testing.assert_array_equal(
        actual=u.action, desired=U_MAX, err_msg="All heaters should be ON"
    )


def test_get_rbc_controller_turns_off_heaters_when_too_hot(rbc_controller):
    T_setpoint = np.ones(N_ROOMS) * 22.0
    # Test case: all rooms above setpoint + deadband -> all heaters OFF
    T_meas = T_setpoint + DEADBAND + 1.0
    u = rbc_controller.get_action(current_state=T_meas, reference=T_setpoint)
    np.testing.assert_array_equal(u.action, 0.0, "All heaters should be OFF")


def test_get_rbc_controller_keeps_heating_within_deadband(rbc_controller):
    u_max = np.ones(N_ROOMS) * 50.0
    T_setpoint = np.ones(N_ROOMS) * 22.0
    u_prev = u_max.copy()
    rbc_controller._previous_action = u_prev.copy()

    # Test case: rooms within deadband -> heaters unchanged
    T_meas = T_setpoint

    u = rbc_controller.get_action(current_state=T_meas, reference=T_setpoint)
    np.testing.assert_array_equal(u.action, u_prev, "Heaters should remain unchanged")


def test_get_rbc_controller_keeps_cooling_within_deadband(rbc_controller):
    u_min = np.zeros(N_ROOMS)
    T_setpoint = np.ones(N_ROOMS) * 22.0
    u_prev = u_min.copy()
    T_meas = T_setpoint

    rbc_controller._previous_action = u_prev.copy()

    u = rbc_controller.get_action(current_state=T_meas, reference=T_setpoint)

    assert np.array_equal(u.action, u_prev), "Heaters should remain unchanged"


def test_get_rbc_controller_mixed_conditions(rbc_controller):
    T_setpoint = np.ones(N_ROOMS) * 22.0

    # Test case: mixed conditions
    T_meas = np.array([19.0, 21.6, 22.4, 23.5, 25.0])

    rbc_controller._set_active()
    u = rbc_controller.get_action(current_state=T_meas, reference=T_setpoint)

    expected_u = np.array([50.0, 50.0, 50.0, 0.0, 0.0])

    np.testing.assert_array_equal(u.action, expected_u, "Mixed heater states incorrect")
