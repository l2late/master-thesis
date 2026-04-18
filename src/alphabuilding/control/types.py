import itertools
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal, Protocol

import control as ct
import jaxtyping
import numpy as np
import scipy.signal

ControlAction = jaxtyping.Float[np.ndarray, "actuators"]
ControlLimit = jaxtyping.Float[np.ndarray, "actuators"]
ControlActionTrajectory = jaxtyping.Float[np.ndarray, "time actuators"]
IsActiveControl = jaxtyping.Bool[np.ndarray, "actuators"]
State = jaxtyping.Float[np.ndarray, "states"]
SystemMatrix = jaxtyping.Float[np.ndarray, "states states"]
ObserverGain = jaxtyping.Float[np.ndarray, "states outputs"]
InputMatrix = jaxtyping.Float[np.ndarray, "states actuators"]
OutputMatrix = jaxtyping.Float[np.ndarray, "outputs states"]
FeedthroughMatrix = jaxtyping.Float[np.ndarray, "outputs actuators"]
Output = jaxtyping.Float[np.ndarray, "outputs"]
Reference = jaxtyping.Float[np.ndarray, "references"]
ReferenceTrajectory = jaxtyping.Float[np.ndarray, "time references"]
Disturbance = jaxtyping.Float[np.ndarray, "disturbances"]
DisturbanceForecast = jaxtyping.Float[np.ndarray, "time disturbances"]
TemperatureBounds = jaxtyping.Float[np.ndarray, "rooms 2"]
TemperatureLimitTrajectory = jaxtyping.Float[np.ndarray, "time rooms"]
TemperatureBoundsTrajectory = jaxtyping.Float[np.ndarray, "time rooms 2"]
SlackWeights = jaxtyping.Float[np.ndarray, "outputs"]
ObserverInput = jaxtyping.Float[np.ndarray, "actuators+disturbances"]


@dataclass(frozen=True)
class ControllerOutput:
    action: ControlAction
    action_trajectory: ControlActionTrajectory | None = None
    solver_status: str | None = None
    solve_time_sec: float | None = None
    solver_num_iters: int | None = None
    solver_name: str | None = None


class Controller(Protocol):
    def get_action(
        self,
        *,
        current_state: State,
        reference: np.ndarray | None = None,
        disturbance: np.ndarray | None = None,
        room_temperature_soft_bounds: TemperatureBoundsTrajectory | None = None,
    ) -> ControllerOutput: ...

    def reset(self) -> None: ...


TimeUnit = Literal["seconds", "hours"]


@dataclass(frozen=True)
class TimedStateSpace:
    """
    Wrapper for LTI systems that enforces explicit time units.

    Attributes:
        system: The underlying control or scipy state-space object.
        dt: The sampling time in the current `time_unit`.
        time_unit: The unit of time for the system's dynamics and dt.
    """

    system: scipy.signal.StateSpace | ct.StateSpace
    dt: float
    time_unit: TimeUnit

    @property
    def dt_in_seconds(self) -> float:
        """Returns the sampling time in seconds, regardless of the stored unit."""
        if self.time_unit == "seconds":
            return self.dt
        return self.dt * 3600.0

    @property
    def dt_in_hours(self) -> float:
        """Returns the sampling time in hours, regardless of the stored unit."""
        if self.time_unit == "hours":
            return self.dt
        return self.dt / 3600.0

    def to_seconds(self) -> "TimedStateSpace":
        """Returns a new TimedStateSpace with the system defined in seconds."""
        if self.time_unit == "seconds":
            return self

        new_dt = self.dt_in_seconds

        # For Discrete Time systems, the A, B, C, D matrices are invariant
        # to the unit label of dt. We only need to update the metadata.
        if isinstance(self.system, ct.StateSpace):
            new_sys = ct.ss(
                self.system.A,
                self.system.B,
                self.system.C,
                self.system.D,
                dt=new_dt,
                inputs=self.system.input_labels,
                outputs=self.system.output_labels,
                name=self.system.name,
            )
        else:
            # Fallback for scipy or other types
            new_sys = scipy.signal.StateSpace(
                self.system.A, self.system.B, self.system.C, self.system.D, dt=new_dt
            )

        assert isinstance(new_sys, ct.StateSpace), (
            "Model creation failed: Expected LTI StateSpace"
        )

        return TimedStateSpace(new_sys, new_dt, "seconds")

    def to_hours(self) -> "TimedStateSpace":
        """Returns a new TimedStateSpace with the system defined in hours."""
        if self.time_unit == "hours":
            return self

        new_dt = self.dt_in_hours

        if isinstance(self.system, ct.StateSpace):
            new_sys = ct.ss(
                self.system.A,
                self.system.B,
                self.system.C,
                self.system.D,
                dt=new_dt,
                inputs=self.system.input_labels,
                outputs=self.system.output_labels,
                name=self.system.name,
            )
        else:
            new_sys = scipy.signal.StateSpace(
                self.system.A, self.system.B, self.system.C, self.system.D, dt=new_dt
            )

        assert isinstance(new_sys, ct.StateSpace), (
            "Model creation failed: Expected LTI StateSpace"
        )
        return TimedStateSpace(new_sys, new_dt, "hours")


class SimulationPhase(str, Enum):
    WARMUP = "warmup"
    EVALUATION = "evaluation"


@dataclass(frozen=True)
class SimulationConfig:
    plant_step_length_seconds: int = 30
    controller_step_length_seconds: int = 15 * 60
    warmup_steps: int = 1
    eval_steps: int = 1


@dataclass(frozen=True)
class MpcConfig:
    model_checkpoint: Path
    horizon: int
    slack_weights: SlackWeights
    R_weights: ControlAction
    margins: ControlAction | None = None


@dataclass(frozen=True)
class MpcSimulationConfig:
    mpc: MpcConfig
    simulation: SimulationConfig


def generate_sweep_runs(
    model_checkpoints: list[Path],
    horizons: list[int],
    slack_weights: list[SlackWeights],
    R_weights: list[ControlAction],
    simulation_config: SimulationConfig,
) -> list[MpcSimulationConfig]:

    runs = []
    # Cartesian product of all your sweep axes
    combinations = itertools.product(
        model_checkpoints, horizons, slack_weights, R_weights
    )

    for chkpt, h, s, r in combinations:
        mpc_config = MpcConfig(
            model_checkpoint=chkpt, horizon=h, slack_weight=s, R_weight=r
        )
        mpc_simulation_config = MpcSimulationConfig(
            mpc=mpc_config,
            simulation=simulation_config,
        )
        runs.append(mpc_simulation_config)

    return runs


@dataclass
class AgentInputs:
    """Encapsulates all signals arriving at the controller at the current timestep."""

    step: int
    y_meas: Output  # Current measured outputs (e.g., room temperatures)
    d_meas: Disturbance  # Current measured disturbances (Tamb, SolRad)
    # Forecasts (can be None for RBC)
    reference: Reference | None = None
    d_forecast: DisturbanceForecast | None = None
    bounds_forecast: TemperatureBoundsTrajectory | None = None
