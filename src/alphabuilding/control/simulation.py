import logging
from dataclasses import fields
from typing import Callable

import einops as eo
import numpy as np
import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from alphabuilding import constants as global_config
from alphabuilding.control.brcm_building import (
    BRCMBuildingSimulator,
)
from alphabuilding.control.controllers import EconomicMPCController, RbcController
from alphabuilding.control.state_estimation import (
    AugmentedLuenbergerObserver,
    FilteringLuenbergerObserver,
)
from alphabuilding.control.types import (
    AgentInputs,
    Controller,
    SimulationConfig,
    SimulationPhase,
)
from alphabuilding.domain.df_schemas import (
    ControllerInput,
    SimulationResult,
)
from alphabuilding.utils.logging_config import sim_time_filter

logger = logging.getLogger(__name__)
NP_ROOM_AREAS = np.array(global_config.ROOM_AREAS)


def resample_controller_inputs_to_plant_dt(
    df: DataFrame[ControllerInput],
    plant_dt_sec: int,
    steps: int,
) -> pd.DataFrame:
    """Resample controller inputs to match plant timestep.
    Args:
        df: input dataframe with controller inputs and disturbances at controller timestep frequency.
        plant_dt_sec: frequency in seconds of the output dataframe, which should match the plant timestep.
        steps: number of steps needed in the output dataframe

    Returns:
        DataFrame with index at plant timestep frequency and columns for disturbances and constraints, resampled from the input dataframe.
        Disturbances are interpolated using time interpolation, while constraints are forward-filled to ensure they are always defined at the plant timestep frequency.
    """

    assert plant_dt_sec > 0, "Plant timestep must be positive"
    df_freq_sec = (df.index[1] - df.index[0]).total_seconds()
    input_df_steps_needed = int(steps * (plant_dt_sec / df_freq_sec))
    assert len(df) >= input_df_steps_needed, (
        f"Input dataframe must have at least {input_df_steps_needed} rows for the simulation but has only {len(df)} rows"
    )

    sim_start_time = df.index[0]
    high_freq_index = pd.date_range(
        start=sim_start_time, periods=steps, freq=f"{plant_dt_sec}s"
    )

    dist_cols = ["Tamb", "SolRad"]
    df_high_freq = df[dist_cols].reindex(high_freq_index).interpolate(method="time")

    constr_cols = ["Tmin", "Tmax"]
    df_high_freq[constr_cols] = df[constr_cols].reindex(high_freq_index).ffill()

    assert isinstance(df_high_freq, pd.DataFrame), "Index must be DatetimeIndex"
    return df_high_freq


def _validate_mpc_simulation_inputs(
    plant: BRCMBuildingSimulator,
    controller: EconomicMPCController,
    sim_steps: int,
    df: DataFrame[ControllerInput],
) -> int:
    # Ensure controller step is a multiple of plant step
    assert controller.dt_in_seconds % plant.dt_in_seconds == 0, (
        "Controller dt must be exact multiple of Plant dt"
    )
    ratio = int(controller.dt_in_seconds // plant.dt_in_seconds)
    controller_sim_steps = sim_steps // ratio

    length_forecast = len(df)
    assert controller_sim_steps + controller.horizon <= length_forecast, (
        f"Disturbance forecast {length_forecast} is too short for given controller simulation steps ({controller_sim_steps}) and controller horizon ({controller.horizon}). Mismatch: {length_forecast - controller_sim_steps - controller.horizon}"
    )

    # validate input dataframe
    n_nans = df.isna().sum().sum()
    assert n_nans == 0, f"Dataframe contains {n_nans} NaN values"

    ControllerInput.validate(df)

    return ratio


# Add simulation phase column
def add_simulation_phase_column(
    df: pd.DataFrame, warmup_steps: int, eval_steps: int
) -> pd.DataFrame:
    """Adds a 'simulation_phase' column to the DataFrame indicating whether each row corresponds to the warmup or evaluation phase of the simulation."""
    phase = np.array(
        [SimulationPhase.WARMUP] * warmup_steps
        + [SimulationPhase.EVALUATION] * eval_steps
        + [SimulationPhase.EVALUATION],  # ZOH padding row matches evaluation phase
        dtype=object,
    )
    df["simulation_phase"] = pd.Categorical(phase, categories=list(SimulationPhase))
    return df


class DataclassRecorder:
    def __init__(self, n_steps: int):
        self.n_steps = n_steps
        # Stores our dynamically created numpy arrays
        self.data: dict[str, np.ndarray] = {}

    def record(self, *, index: int, instance) -> None:
        """Dynamically iterates over any dataclass and records its fields."""
        for field in fields(instance):
            name = field.name
            val = getattr(instance, name)

            # Skip None values. We wait for a real value to deduce the shape/type.
            if val is None:
                continue

            # If we haven't seen this field yet, initialize the array!
            if name not in self.data:
                if isinstance(val, (int, float)):
                    # Use float so we can pad missing steps with np.nan
                    self.data[name] = np.full(self.n_steps, np.nan, dtype=float)
                elif isinstance(val, np.ndarray):
                    # Magically pre-allocate multidimensional arrays!
                    # e.g., for action_trajectory, shape becomes (n_steps, horizon, actuators)
                    shape = (self.n_steps, *val.shape)
                    self.data[name] = np.full(shape, np.nan, dtype=val.dtype)
                else:
                    # Fallback for strings (like solver_status) or complex objects
                    self.data[name] = np.full(self.n_steps, None, dtype=object)

            # Insert the value at timestep k
            self.data[name][index] = val


# Add recorded controller outputs (like solver status, predicted trajectories, etc.) to the DataFrame.
def add_recorded_controller_outputs_to_df(
    df: pd.DataFrame, recorder: DataclassRecorder
) -> pd.DataFrame:
    """Takes the recorded controller outputs from the DataclassRecorder and adds them as columns to the DataFrame. Only 1D arrays are added to keep the DataFrame flat and clean. Multidimensional arrays (like predicted trajectories) are not added directly but could be processed separately if needed."""
    for name, array in recorder.data.items():
        # Only attach 1D arrays to the DataFrame to keep it flat and clean
        if array.ndim == 1:
            # if dtype is str, then convert to Categorical for memory efficiency
            if array.dtype == object:
                array = pd.Categorical(array)
            df[f"controller_{name}"] = array
    return df


class MultiRateControlAgent:
    """
    Handles independent multi-rate execution of Controllers and Observers,
    buffering fast signals to accurately update slow discrete observers.
    """

    def __init__(
        self,
        controller: Controller,
        observer: AugmentedLuenbergerObserver,
        ctrl_ratio: int,
        obs_ratio: int,
    ):
        self.controller = controller
        self.observer = observer

        self.ctrl_ratio = ctrl_ratio
        self.obs_ratio = obs_ratio

        self._cached_controller_output = None

        # Buffer to accumulate fast plant inputs (u, d) over the slow observer interval
        self._u_buffer = []
        self._d_buffer = []

    def clear_cache(self):
        """Used when hotswapping controllers to force a fresh computation."""
        self._cached_controller_output = None

    def get_action(self, inputs: AgentInputs):
        # 1. SLOW OBSERVER UPDATE (Executes only on the observer boundary)
        if inputs.step > 0 and inputs.step % self.obs_ratio == 0:
            # 15-min Luenberger equations expect a single u_k; use mean over fast steps
            u_mean = np.mean(np.stack(self._u_buffer, axis=0), axis=0)
            d_mean = np.mean(np.stack(self._d_buffer, axis=0), axis=0)
            u_prev = np.concatenate([u_mean, d_mean])

            self.observer.update(u_prev=u_prev, y_current=inputs.y_meas, x_true=None)

            self._u_buffer.clear()
            self._d_buffer.clear()

        # 2. Build controller state and (optionally) disturbance estimate
        if isinstance(self.controller, EconomicMPCController):
            current_state = self.observer.x_hat
            # disturbance estimate from augmented observer; d_hat is shape (1,)
            current_d_est = (
                self.observer.d_hat if hasattr(self.observer, "d_hat") else None
            )
        else:
            current_state = inputs.y_meas
            current_d_est = None

        # 3. CONTROLLER UPDATE (Executes on controller boundary, ZOH otherwise)
        if inputs.step % self.ctrl_ratio == 0 or self._cached_controller_output is None:
            if isinstance(self.controller, EconomicMPCController):
                self._cached_controller_output = self.controller.get_action(
                    current_state=current_state,
                    reference=inputs.reference,
                    disturbance=inputs.d_forecast,
                    room_temperature_soft_bounds=inputs.bounds_forecast,
                    d_est=current_d_est,  # only MPC sees this
                )
            else:
                self._cached_controller_output = self.controller.get_action(
                    current_state=current_state,
                    reference=inputs.reference,
                    disturbance=inputs.d_forecast,
                    room_temperature_soft_bounds=inputs.bounds_forecast,
                )

        # 4. Buffer for next observer interval
        self._u_buffer.append(self._cached_controller_output.action)
        self._d_buffer.append(inputs.d_meas)

        return self._cached_controller_output


@pa.check_types
def run_simulation(
    *,
    plant: BRCMBuildingSimulator,
    warmup_controller: RbcController,
    eval_controller: Controller,
    observer: FilteringLuenbergerObserver | AugmentedLuenbergerObserver,
    df: DataFrame[ControllerInput],
    config: SimulationConfig,
    # Optional callback function that gets called at each simulation step with the current step number and context for real-time monitoring or visualization
    optuna_pruning_callback: Callable | None = None,
) -> DataFrame[SimulationResult]:

    ControllerInput.validate(df)

    warmup_steps = config.warmup_steps
    eval_steps = config.eval_steps
    controller_dt_sec = config.controller_step_length_seconds
    n_rooms = 5

    # ------------------ TIMING VALIDATION ------------------
    assert controller_dt_sec % plant.dt_in_seconds == 0, (
        "Controller dt must be exact multiple of Plant dt"
    )
    ratio = int(controller_dt_sec // plant.dt_in_seconds)
    assert warmup_steps % ratio == 0, (
        "Warmup phase must end exactly on a slow controller timestep boundary to prevent phase misalignment!"
    )
    # -------------------------------------------------------

    # Reset states to ensure clean start before simulation
    plant.reset()
    warmup_controller.reset()
    eval_controller.reset()
    # Observer only estimates room temperatures, not disturbances
    observer.reset(x0=plant.x[: observer.nx])

    total_sim_steps = warmup_steps + eval_steps

    # Pre-Allocate arrays
    controller_output_recorder = DataclassRecorder(total_sim_steps + 1)
    u_W_per_m2_traj = np.zeros((total_sim_steps, n_rooms))
    room_temps_traj = np.zeros((total_sim_steps + 1, n_rooms))
    # observer_error_traj = np.zeros((total_sim_steps, observer.ny))
    observer_prior_output_error_traj = np.zeros((total_sim_steps, observer.ny))
    observer_post_output_error_traj = np.zeros((total_sim_steps, observer.ny))

    # Store initial state in trajectory array
    room_temps_traj[0, :] = plant.x[:n_rooms]

    # Prepare Interpolated Plant-Frequency Data
    horizon = (
        eval_controller.horizon
        if isinstance(eval_controller, EconomicMPCController)
        else 0
    )
    total_input_data_steps_needed = total_sim_steps + horizon * ratio + 1

    # High frequency (plant timestep) DataFrame for disturbances and constraints, resampled from the input controller-frequency DataFrame
    df_hf = resample_controller_inputs_to_plant_dt(
        df=df, plant_dt_sec=plant.dt_in_seconds, steps=total_input_data_steps_needed
    )

    t_amb = df_hf["Tamb"].to_numpy()
    solar_rad = df_hf["SolRad"].to_numpy()
    Tmin = df_hf["Tmin"].to_numpy()
    Tmax = df_hf["Tmax"].to_numpy()
    assert np.all(Tmax - 2 > Tmin), (
        "Tmax - 2 must be greater than Tmin at all timesteps in the input DataFrame"
    )

    # Fast Reference Arrays (RBC only)
    warmup_reference_hf = (
        eo.repeat(Tmin, "u -> u zone", zone=5) + warmup_controller.deadband
    )
    eval_reference_hf = eo.repeat(Tmin, "u -> u zone", zone=5) + getattr(
        eval_controller, "deadband", 0
    )

    # Slow Forecast Arrays (MPC only)
    mpc_disturbance_forecasts, mpc_room_temperature_soft_bounds = None, None
    if isinstance(eval_controller, EconomicMPCController):
        _validate_mpc_simulation_inputs(plant, eval_controller, eval_steps, df)

        mpc_bounds = eo.repeat(
            df[["Tmin", "Tmax"]].to_numpy(),
            "time constraint -> time room constraint",
            room=5,
        )
        mpc_bounds = np.lib.stride_tricks.sliding_window_view(
            mpc_bounds, window_shape=eval_controller.horizon, axis=0
        )
        mpc_room_temperature_soft_bounds = eo.rearrange(
            mpc_bounds, "time room constraint horizon -> time horizon room constraint"
        )

        mpc_disturbance_forecasts = np.lib.stride_tricks.sliding_window_view(
            df[["Tamb", "SolRad"]].to_numpy(),
            window_shape=eval_controller.horizon,
            axis=0,
        )
        mpc_disturbance_forecasts = eo.rearrange(
            mpc_disturbance_forecasts,
            "time disturbance horizon -> time horizon disturbance",
        )

    # Initialize the Agent
    # observer ALWAYS runs at `ratio`. Warmup RBC runs at 1 (fast).
    agent = MultiRateControlAgent(
        controller=warmup_controller, observer=observer, ctrl_ratio=1, obs_ratio=ratio
    )

    ## --------------------------------------------------------------------------------------------
    ## UNIFIED SIMULATION LOOP
    ## --------------------------------------------------------------------------------------------
    for step in range(total_sim_steps):
        is_warmup = step < warmup_steps

        # log only on controller boundaries, not every plant step
        if step % ratio == 0:
            sim_time_filter.sim_time = df_hf.index[step].isoformat(timespec="minutes")
            logger.debug("step=%d phase=%s", step, "warmup" if is_warmup else "eval")

        # Fetch current physical state
        current_y = plant.x[:n_rooms]
        current_d = np.array([t_amb[step].item(), solar_rad[step].item()])

        # HOTSWAP LOGIC at Phase Boundary
        if step == warmup_steps:
            agent.controller = eval_controller
            agent.ctrl_ratio = (
                ratio if isinstance(eval_controller, EconomicMPCController) else 1
            )

            agent.clear_cache()  # Force MPC to compute immediately

        # Route the context correctly
        ## During warmup, we always use the RBC reference and ignore forecasts and constraints since RBC doesn't use them.
        if is_warmup:
            current_ref = warmup_reference_hf[step]
            current_d_forecast = None
            current_bounds = None
        ## During evaluation, the context depends on the controller type
        elif isinstance(eval_controller, RbcController):
            current_ref = eval_reference_hf[step]
            current_d_forecast = None
            current_bounds = None
        elif isinstance(eval_controller, EconomicMPCController):
            current_ref = None
            ctrl_step = step // ratio
            current_d_forecast = mpc_disturbance_forecasts[ctrl_step]
            current_bounds = mpc_room_temperature_soft_bounds[ctrl_step]

        inputs = AgentInputs(
            step=step,
            y_meas=current_y,
            d_meas=current_d,
            reference=current_ref,
            d_forecast=current_d_forecast,
            bounds_forecast=current_bounds,
        )

        # Agent Execution
        controller_output = agent.get_action(inputs)
        u_W_per_m2 = controller_output.action

        # Record
        controller_output_recorder.record(index=step, instance=controller_output)
        u_W_per_m2_traj[step, :] = u_W_per_m2
        # observer_error_traj[step, :] = observer.innovation
        observer_prior_output_error_traj[step, :] = observer.prior_output_error
        observer_post_output_error_traj[step, :] = observer.posterior_output_error

        # Step Plant
        room_temps = plant.simulate_one_step(
            u_radiators=u_W_per_m2,
            t_amb=t_amb[step].item(),
            solar_rad=solar_rad[step].item(),
        )
        room_temps_traj[step + 1, :] = room_temps

        if optuna_pruning_callback is not None:
            optuna_pruning_callback(
                step=step,
                y=current_y,  # already available
                tmin=Tmin[step : step + 1],  # scalar slice from pre-computed array
                tmax=Tmax[step : step + 1],
            )

    ## --------------------------------------------------------------------------------------------
    # ASSEMBLE RESULTS
    df_hf = df_hf.iloc[: total_sim_steps + 1]

    y_cols = [f"y{i + 1}" for i in range(n_rooms)]
    df_hf[y_cols] = room_temps_traj

    u_cols = [f"u{i + 1}" for i in range(n_rooms)]
    u_Watt_per_m2_traj_padded = np.vstack([u_W_per_m2_traj, u_W_per_m2_traj[-1, :]])
    df_hf[u_cols] = u_Watt_per_m2_traj_padded * NP_ROOM_AREAS

    # Prior output error  (was obs_err{i})
    prior_e_cols = [f"obs_prior_err{i + 1}" for i in range(n_rooms)]  # renamed
    obs_prior_output_error_padded = np.vstack(
        [observer_prior_output_error_traj, np.full((1, observer.ny), np.nan)]
    )
    df_hf[prior_e_cols] = obs_prior_output_error_padded

    # Posterior output error  (NEW)
    post_e_cols = [f"obs_post_err{i + 1}" for i in range(n_rooms)]
    obs_post_output_error_padded = np.vstack(
        [observer_post_output_error_traj, np.full((1, observer.ny), np.nan)]
    )
    df_hf[post_e_cols] = obs_post_output_error_padded

    df_hf = add_simulation_phase_column(
        df_hf, warmup_steps=warmup_steps, eval_steps=eval_steps
    )
    df_hf = add_recorded_controller_outputs_to_df(df_hf, controller_output_recorder)

    SimulationResult.validate(df_hf)
    df_hf.index.name = "datetime"

    return df_hf
