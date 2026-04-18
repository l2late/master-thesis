from dataclasses import asdict

import einops as eo
import numpy as np
import numpy.testing as npt
import pandas as pd
import pytest
import scipy.signal
from einops import reduce, repeat
from pandera.typing import DataFrame

from alphabuilding.constants import ROOM_AREAS
from alphabuilding.control.brcm_building import (
    BRCMBuildingSimulator,
)
from alphabuilding.control.controllers import EconomicMPCController
from alphabuilding.control.simulation import run_mpc_simulation
from alphabuilding.control.types import TimedStateSpace
from alphabuilding.control.utils import (
    add_comfort_bounds_for_simulation,
    get_controller_input_df,
)
from alphabuilding.domain.df_schemas import ControllerInput

PLANT_DT_SEC = 30  # plant simulation time step in seconds
MPC_DT_SEC = 15 * 60  # MPC time step in seconds
MPC_HORIZON = 2
INITIAL_TEMPERATURE = 19.0
N_ROOMS = 5
N_INPUTS = N_ROOMS  # one radiator input per room
N_DISTURBANCES = 2  # ambient temperature and solar radiation

U_MIN = 0.0
U_MAX_W_PER_M2 = 50.0
NP_ROOM_AREAS = np.array(ROOM_AREAS)
U_MIN_WATTS_PER_ROOM = U_MIN * NP_ROOM_AREAS
U_MAX_WATTS_PER_ROOM = U_MAX_W_PER_M2 * NP_ROOM_AREAS
Y_COLS = [f"y{i + 1}" for i in range(N_ROOMS)]
U_COLS = [f"u{i + 1}" for i in range(N_ROOMS)]


@pytest.fixture(scope="session")
def dissipative_discrete_lti_model(
    nx=N_ROOMS, nu=N_INPUTS, nd=N_DISTURBANCES
) -> TimedStateSpace:
    A = (
        np.eye(nx) * 0.1
    )  # very slightly dissipative to ensure passivity and avoid numerical issues with pure integrator
    Bu = np.eye(nx, nu) * 0.00001  # very small input gain
    Bd = np.ones((nx, nd)) * 0.000001  # very small disturbance gain
    B = np.hstack((Bu, Bd))
    C = np.eye(nx)
    D = np.zeros((nx, nu + nd))
    ss = TimedStateSpace(
        system=scipy.signal.StateSpace(A, B, C, D, dt=MPC_DT_SEC),
        dt=MPC_DT_SEC,
        time_unit="seconds",
    )
    return ss


@pytest.fixture
def empc_controller(internal_model, scalers):
    mpc_controller = EconomicMPCController(
        model=internal_model,
        horizon=MPC_HORIZON,
        R_weight=0.01,
        slack_weight=100.0,
        u_min_physical=U_MIN_WATTS_PER_ROOM,
        u_max_physical=U_MAX_WATTS_PER_ROOM,
        scalers=scalers,
    )
    return mpc_controller


@pytest.fixture
def simulator(mat_file_path):
    simulator = BRCMBuildingSimulator.from_mat_file(
        mat_file_path, initial_temp=INITIAL_TEMPERATURE
    )
    return simulator


def test_economic_mpc_with_passive_model_initialized_too_warm_does_not_heat(
    dissipative_discrete_lti_model, scalers
):
    model = dissipative_discrete_lti_model
    horizon = 10
    mpc_controller = EconomicMPCController(
        model=model,
        horizon=horizon,
        R_weight=1,
        slack_weight=100.0,
        u_min_physical=np.array(U_MIN_WATTS_PER_ROOM),
        u_max_physical=np.array(U_MAX_WATTS_PER_ROOM),
        scalers=scalers,
    )

    x_current = np.ones((mpc_controller.nx,)) * 30.0

    disturbance_forecast = np.ones((horizon, mpc_controller.nd)) * 30.0

    Tmin_future = np.ones((horizon, N_ROOMS)) * 18.0
    Tmax_future = np.ones((horizon, N_ROOMS)) * 20.0
    room_temperature_soft_bounds = np.stack((Tmin_future, Tmax_future), axis=-1)

    action = mpc_controller.get_action(
        current_state=x_current,
        disturbance=disturbance_forecast,
        room_temperature_soft_bounds=room_temperature_soft_bounds,
    )
    u_opt = action.action_trajectory

    assert u_opt.shape == (horizon, mpc_controller.nu)
    assert u_opt == pytest.approx(np.zeros_like(u_opt), abs=1e-3), (
        "MPC should not apply heating when model is dissipative and current temperature is above comfort bounds"
    )


def test_economic_mpc_with_passive_model_initialized_too_cold_does_heat_max(
    dissipative_discrete_lti_model, scalers
):
    # ARRANGE
    model = dissipative_discrete_lti_model
    horizon = 2
    mpc_controller = EconomicMPCController(
        model=model,
        horizon=horizon,
        R_weight=1e-4,  # very low weight on input usage, to encourage maximum heating
        slack_weight=100.0,  # high weight on slack to avoid comfort violations
        u_min_physical=np.array(U_MIN_WATTS_PER_ROOM),
        u_max_physical=np.array(U_MAX_WATTS_PER_ROOM),
        scalers=scalers,
    )

    Tmin_future = np.ones((horizon, N_ROOMS)) * 18.0
    Tmax_future = np.ones((horizon, N_ROOMS)) * 20.0
    # Set temperature well below comfort bounds
    x_current = np.ones((mpc_controller.nx,)) * 1.0
    disturbance_forecast = np.ones((horizon, mpc_controller.nd)) * 1.0

    # ACT
    control_action = mpc_controller.get_action(
        current_state=x_current,
        disturbance=disturbance_forecast,
        room_temperature_soft_bounds=np.stack((Tmin_future, Tmax_future), axis=-1),
    )
    u_opt = control_action.action_trajectory

    max_heat_per_room = repeat(U_MAX_WATTS_PER_ROOM, "n -> h n", h=horizon)
    assert u_opt.shape == (horizon, mpc_controller.nu)
    assert u_opt == pytest.approx(max_heat_per_room, abs=1e-1), (
        "MPC should apply full on heating when model is dissipative and state and disturbances are below comfort bounds"
    )


def test_economic_mpc_compute_control_action(internal_model, scalers):
    horizon = 5
    mpc_controller = EconomicMPCController(
        model=internal_model,
        horizon=horizon,
        R_weight=0.01,
        slack_weight=100.0,
        u_min_physical=np.array(U_MIN_WATTS_PER_ROOM),
        u_max_physical=np.array(U_MAX_WATTS_PER_ROOM),
        scalers=scalers,
    )

    x_current = np.random.rand(mpc_controller.nx)

    disturbance_forecast = np.random.rand(horizon, mpc_controller.nd)
    Tmin_future = np.ones((horizon, N_ROOMS)) * 18.0
    Tmax_future = np.ones((horizon, N_ROOMS)) * 24

    u_opt = mpc_controller._solve(
        x0=x_current,
        disturbance_forecast=disturbance_forecast,
        Tmin_traj=Tmin_future,
        Tmax_traj=Tmax_future,
    )

    assert u_opt.shape == (horizon, mpc_controller.nu)

    epsilon = 1e-3
    np.testing.assert_array_less(
        mpc_controller.u_min - epsilon,
        np.min(u_opt, axis=0),
        err_msg="MPC output below minimum control limits",
    )
    np.testing.assert_array_less(
        np.max(u_opt, axis=0),
        mpc_controller.u_max + epsilon,
        err_msg="MPC output above maximum control limits",
    )


def test_mpc_simulation_with_unscaled_controller(simulator, empc_controller):
    control_steps = 2
    sim_steps = control_steps * (15 * 60) // 30
    required_input_length = empc_controller.horizon + control_steps

    # Arrange
    datetime_index = pd.date_range(
        start="2023-01-01", periods=required_input_length, freq="15min"
    )
    control_input_df = pd.DataFrame(index=datetime_index)
    control_input_df["Tmin"] = np.ones(required_input_length) * 18.0
    control_input_df["Tmax"] = np.ones(required_input_length) * 24
    control_input_df["Tamb"] = np.random.rand(required_input_length)
    control_input_df["SolRad"] = np.random.rand(required_input_length)

    # Act
    simulation_result = run_mpc_simulation(
        plant=simulator,
        controller=empc_controller,
        sim_steps=control_steps,
        df=DataFrame[ControllerInput](control_input_df),
    )

    # simulation_result_XXX = run_simulation(
    #     plant=simulator,
    #     controller=empc_controller,
    #     sim_steps=sim_steps,
    #     df=DataFrame[ControllerInput](control_input_df),
    # )

    # assert pd.testing.assert_frame_equal(simulation_result, simulation_result_XXX), (
    #     "run_mpc_simulation and run_simulation should produce the same results when given the same inputs"
    # )

    # Assert
    room_temps = simulation_result[Y_COLS].to_numpy()
    inputs = simulation_result[U_COLS].to_numpy()
    assert room_temps.shape == (sim_steps + 1, N_ROOMS)
    assert inputs.shape == (sim_steps + 1, empc_controller.nu)

    max_inputs_per_room_over_time = inputs.max(axis=0)
    min_inputs_per_room_over_time = inputs.min(axis=0)
    assert np.all(max_inputs_per_room_over_time <= U_MAX_WATTS_PER_ROOM + 1e-3)
    assert np.all(min_inputs_per_room_over_time >= U_MIN_WATTS_PER_ROOM - 1e-3)


def test_mpc_simulation_with_scaled_controller(simulator, empc_controller):
    control_steps = 10
    sim_steps = control_steps * (15 * 60) // 30
    required_input_length = empc_controller.horizon + control_steps

    # Arrange
    datetime_index = pd.date_range(
        start="2023-01-01", periods=required_input_length, freq="15min"
    )
    control_input_df = pd.DataFrame(index=datetime_index)
    control_input_df["Tmin"] = np.ones(required_input_length) * 18.0
    control_input_df["Tmax"] = np.ones(required_input_length) * 24
    control_input_df["Tamb"] = np.random.rand(required_input_length)
    control_input_df["SolRad"] = np.random.rand(required_input_length)

    # Act
    simulation_result = run_mpc_simulation(
        plant=simulator,
        controller=empc_controller,
        sim_steps=control_steps,
        df=DataFrame[ControllerInput](control_input_df),
    )

    # Assert
    room_temps = simulation_result[Y_COLS].to_numpy()
    inputs = simulation_result[U_COLS].to_numpy()
    assert room_temps.shape == (sim_steps + 1, N_ROOMS)
    assert inputs.shape == (sim_steps + 1, empc_controller.nu)

    all_time_max_inputs_per_room = inputs.max(axis=0)
    all_time_min_inputs_per_room = inputs.min(axis=0)
    assert all_time_max_inputs_per_room.shape == (N_ROOMS,)
    assert all_time_min_inputs_per_room.shape == (N_ROOMS,)

    epsilon = 1e-3
    npt.assert_array_less(
        all_time_max_inputs_per_room - epsilon,
        U_MAX_WATTS_PER_ROOM,
        err_msg="Max inputs exceeded upper bound",
    )
    npt.assert_array_less(
        U_MIN_WATTS_PER_ROOM - epsilon,
        all_time_min_inputs_per_room,
        err_msg="Min inputs below lower bound",
    )


# test a scaler accepts inputs of any number of features
def test_scaler_accepts_inputs_of_single_feature(scalers):
    array = np.random.rand(10, 1)

    for name, scaler in asdict(scalers).items():
        transformed = scaler.transform(array)
        inversed = scaler.inverse_transform(transformed)
        assert transformed.shape == array.shape, (
            f"Scaler {name} changed shape on transform"
        )
        assert inversed.shape == array.shape, (
            f"Scaler {name} changed shape on inverse_transform"
        )


# test scaler accepts inputs of any number of features
# why? the same scaler should be me applied to all the features with the same physical quantity. E.g., all zone temperatures
# When transforming or inverse transforming, the scaler should automatically handle multiple features by reshaping -> transforming -> reshaping back
def test_scaler_accepts_inputs_of_multiple_feature(scalers):
    array = np.random.rand(10, 10)

    for name, scaler in asdict(scalers).items():
        transformed = scaler.transform(array)
        inversed = scaler.inverse_transform(transformed)
        assert transformed.shape == array.shape, (
            f"Scaler {name} changed shape on transform"
        )
        assert inversed.shape == array.shape, (
            f"Scaler {name} changed shape on inverse_transform"
        )


# test if the scaled controller wrapper outputs unscaled data in Watts for input to the plant
def test_scaled_controller_wrapper_generated_control_actions_in_watts(
    empc_controller,
):
    x_current = np.random.rand(empc_controller.nx)

    disturbance_forecast = np.random.rand(empc_controller.nd, MPC_HORIZON)
    Tmin_future = np.ones((MPC_HORIZON, N_ROOMS)) * 18.0
    Tmax_future = np.ones((MPC_HORIZON, N_ROOMS)) * 24

    control_action = empc_controller.get_action(
        current_state=x_current,
        disturbance=disturbance_forecast,
        room_temperature_soft_bounds=np.stack((Tmin_future, Tmax_future), axis=-1),
    )

    u_mpc_watts = control_action.action_trajectory

    max_inputs_per_room_over_time = reduce(u_mpc_watts, "time input -> input", "max")
    min_inputs_per_room_over_time = reduce(u_mpc_watts, "time input -> input", "min")

    epsilon = 1e-3
    npt.assert_array_less(
        max_inputs_per_room_over_time,
        U_MAX_WATTS_PER_ROOM + epsilon,
        err_msg="Max inputs exceeded upper bound",
    )
    npt.assert_array_less(
        U_MIN_WATTS_PER_ROOM - epsilon,
        min_inputs_per_room_over_time,
        err_msg="Min inputs below lower bound",
    )
    assert u_mpc_watts.shape == (MPC_HORIZON, empc_controller.nu)


# test scaled controller wrapper output can be applied to the plant simulator without errors
def test_scaled_controller_wrapper_output_compatible_with_plant_simulator(
    simulator, empc_controller
):
    x_current = np.random.rand(empc_controller.nx)

    disturbance_forecast = np.random.rand(MPC_HORIZON, empc_controller.nd)
    Tmin_future = np.ones((MPC_HORIZON, N_ROOMS)) * 18.0
    Tmax_future = np.ones((MPC_HORIZON, N_ROOMS)) * 24

    control_action = empc_controller.get_action(
        current_state=x_current,
        disturbance=disturbance_forecast,
        room_temperature_soft_bounds=np.stack((Tmin_future, Tmax_future), axis=-1),
    )

    u_mpc_watts = control_action.action_trajectory

    # simulate one step with the first control action
    try:
        room_temps = simulator.simulate_one_step(
            u_radiators=u_mpc_watts[0, :],
            t_amb=15.0,
            solar_rad=200.0,
        )
        assert room_temps.shape == (N_ROOMS,)
    except Exception as e:
        pytest.fail(f"Scaled controller output could not be applied to plant: {e}")


# test the scaled mpc controller works in a closed-loop simulation with the plant simulator over multiple steps
def test_scaled_controller_wrapper_closed_loop_simulation(
    simulator, empc_controller, controller_input_df
):
    control_steps = 3
    sim_steps = control_steps * (15 * 60) // 30

    simulation_result = run_mpc_simulation(
        plant=simulator,
        controller=empc_controller,
        sim_steps=control_steps,
        df=controller_input_df,
    )

    room_temps = simulation_result[Y_COLS].to_numpy()
    inputs = simulation_result[U_COLS].to_numpy()

    assert room_temps.shape == (sim_steps + 1, N_ROOMS)
    assert inputs.shape == (sim_steps + 1, empc_controller.nu)

    max_inputs_per_room_over_time = reduce(inputs, "time input -> input", "max")
    min_inputs_per_room_over_time = reduce(inputs, "time input -> input", "min")

    epsilon = 1e-3

    npt.assert_array_less(
        max_inputs_per_room_over_time,
        U_MAX_WATTS_PER_ROOM + epsilon,
        err_msg="Max inputs exceeded upper bound",
    )
    npt.assert_array_less(
        U_MIN_WATTS_PER_ROOM - epsilon,
        min_inputs_per_room_over_time,
        err_msg="Min inputs below lower bound",
    )


def test_add_comfort_bounds_with_disturbances_df_has_no_nans(
    validation_disturbances_df,
):
    disturbances_df = validation_disturbances_df

    n_steps = disturbances_df.shape[0]

    df = add_comfort_bounds_for_simulation(validation_disturbances_df)
    assert df["Tmin"].shape == (n_steps,)
    assert df["Tmin"].shape == (n_steps,)
    tmin_has_nans = bool(df["Tmin"].isna().any())
    assert not tmin_has_nans, "Tmin column contains NaNs"
    tmax_has_nans = bool(df["Tmax"].isna().any())
    assert not tmax_has_nans, "Tmax column contains NaNs"


def test_get_controller_input_df_contains_no_nans(mat_file_path, datamodule):
    controller_input_df = get_controller_input_df(mat_file_path, datamodule)
    assert not bool(controller_input_df.isna().to_numpy().any()), (
        "Controller input DataFrame contains NaNs"
    )


def test_economic_mpc_controller_returns_correct_shape(
    dissipative_discrete_lti_model, scalers
):
    horizon = 2

    disturbances = np.zeros((horizon, N_DISTURBANCES))
    room_temperature_bounds = eo.repeat(
        np.array([15.0, 25.0]),
        "bounds -> horizon rooms bounds",
        horizon=horizon,
        rooms=N_ROOMS,
    )

    mpc = EconomicMPCController(
        model=dissipative_discrete_lti_model,
        horizon=horizon,
        R_weight=1.0,
        slack_weight=1000.0,
        u_min_physical=np.zeros(N_ROOMS),
        u_max_physical=np.ones(N_ROOMS),
        scalers=scalers,
    )
    x0 = np.ones(N_ROOMS) * 20.0
    control_action = mpc.get_action(
        current_state=x0,
        disturbance=disturbances,
        room_temperature_soft_bounds=room_temperature_bounds,
    )
    u_opt = control_action.action
    assert u_opt.shape == (N_INPUTS,), "Optimal control action has incorrect shape"


def test_scaled_economic_mpc_controller_respects_control_limits(
    dissipative_discrete_lti_model, scalers
):
    horizon = 24
    controller = EconomicMPCController(
        model=dissipative_discrete_lti_model,
        horizon=horizon,
        R_weight=1.0,  # physical units
        slack_weight=1000.0,  # physical units
        u_min_physical=U_MIN_WATTS_PER_ROOM,
        u_max_physical=U_MAX_WATTS_PER_ROOM,
        scalers=scalers,
    )
    control_action = controller.get_action(
        current_state=np.ones(N_ROOMS) * 20.0,
        disturbance=np.ones((horizon, N_DISTURBANCES)) * 20.0,
        room_temperature_soft_bounds=eo.repeat(
            np.array([18.0, 24.0]),
            "bounds -> horizon rooms bounds",
            horizon=horizon,
            rooms=N_ROOMS,
        ),
    )
    action_trajectory = control_action.action_trajectory
    assert action_trajectory is not None, "MPC did not return an action trajectory"
    assert np.all(action_trajectory <= U_MAX_WATTS_PER_ROOM), (
        "MPC output exceeds max control limits"
    )
    assert np.all(action_trajectory >= U_MIN_WATTS_PER_ROOM), (
        "MPC output below min control limits"
    )
