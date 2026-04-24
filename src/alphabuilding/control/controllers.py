import logging

import cvxpy as cp
import jaxtyping
import numpy as np
from beartype import beartype as typechecker

import alphabuilding.constants as global_config
from alphabuilding.control.types import (
    ControlAction,
    ControlActionTrajectory,
    Controller,
    ControllerOutput,
    DisturbanceForecast,
    IsActiveControl,
    Reference,
    SlackWeights,
    State,
    TemperatureBoundsTrajectory,
    TemperatureLimitTrajectory,
    TimedStateSpace,
)
from alphabuilding.domain.types import Scalers

logger = logging.getLogger(__name__)


class MPCSolverError(Exception):
    """Raised when the MPC solver fails to find a valid solution."""

    def __init__(self, message: str, status: str | None = None):
        super().__init__(message)
        self.status = status


class RbcController(Controller):
    @jaxtyping.jaxtyped(typechecker=typechecker)
    def __init__(
        self,
        *,
        n_actuators: int = 5,
        u_max: ControlAction | None = None,
        u_min: ControlAction | None = None,
        deadband: ControlAction | None = None,
    ):
        if u_max is None:
            u_max = np.ones(n_actuators) * 50.0
        if u_min is None:
            u_min = np.zeros(n_actuators)
        if deadband is None:
            deadband = np.ones(n_actuators) * 0.5

        assert (
            u_max.shape == (n_actuators,)
            and u_min.shape == (n_actuators,)
            and deadband.shape == (n_actuators,)
        ), "u_max, u_min, and deadband must have shape (n_actuators,)"
        assert np.all(deadband >= 0), "deadband values must be non-negative"
        assert np.all(u_max >= u_min), "u_max must be greater than or equal to u_min"

        self.n_actuators = n_actuators
        self.u_max = u_max
        self.u_min = u_min
        self.deadband = deadband
        self._previous_action: ControlAction | None = None
        self._is_active: np.ndarray = np.zeros(n_actuators, dtype=bool)

    @jaxtyping.jaxtyped(typechecker=typechecker)
    def get_action(
        self,
        *,
        current_state: State,
        reference: Reference | None = None,
        disturbance=None,
        room_temperature_soft_bounds=None,
    ) -> ControllerOutput:

        # Hysteresis logic using self._previous_action and self._is_active
        error = reference - current_state
        action = np.zeros(self.n_actuators)

        for i in range(self.n_actuators):
            if error[i] > self.deadband[i] and not self._is_active[i]:
                action[i] = self.u_max[i]
                self._is_active[i] = True
            elif error[i] < -self.deadband[i] and self._is_active[i]:
                action[i] = self.u_min[i]
                self._is_active[i] = False
            elif self._previous_action is not None:
                action[i] = self._previous_action[i]

        self._previous_action = action

        control_output = ControllerOutput(action=action)
        return control_output

    def reset(self) -> None:
        self._previous_action = None
        self._is_active = np.zeros(self.n_actuators, dtype=bool)

    def _set_active(self) -> None:
        self._previous_action = self.u_max.copy()
        self._is_active = np.ones(self.n_actuators, dtype=bool)

    def _set_inactive(self) -> None:
        self._previous_action = self.u_min.copy()
        self._is_active = np.zeros(self.n_actuators, dtype=bool)

    @property
    def is_active(self) -> IsActiveControl:
        return self._is_active


NP_ROOM_AREAS = np.array(global_config.ROOM_AREAS)


class EconomicMPCController(Controller):
    def __init__(
        self,
        *,
        model: TimedStateSpace,
        horizon: int,
        R_weights: ControlAction,
        slack_weights: SlackWeights,
        lambda_du: float,
        u_min_physical: ControlAction,
        u_max_physical: ControlAction,
        scalers: Scalers,
        debug: bool = True,
        margins: ControlAction | None = None,
    ):
        """
        Economic MPC controller for building temperature control.
        Args:
            model: Discrete-time state-space model of the building in SCALED space
            horizon: MPC prediction horizon (number of time steps at the model sampling time).
            R_weight: Weight for energy cost in the objective
            slack_weight: Weight for constraint violation penalties in the objective.
            lambda_du: Weight on the control input rate-of-change penalty (smoothness).
            u_min_physical: Minimum control action in physical units as required by the plant (Watts per m2)
            u_max_physical: Maximum control action in physical units as required by the plant (Watts per m2)
            scalers: Scalers for normalizing inputs/outputs to the MPC's internal model space.
            debug: If True, print detailed debug information during solve.
            margins: Optional safety margin to tighten the temperature constraints (in degrees Celsius). This margin is added to T_min and subtracted from T_max to create a buffer zone, helping to ensure that the actual room temperatures stay within the original specified limits even in the presence of model inaccuracies or disturbances.
        """

        self.debug = debug
        self.scalers = scalers

        model_in_seconds = model.to_seconds()
        sys = model_in_seconds.system
        assert sys.dt is not None and sys.A is not None and sys.B is not None, (
            "Model must be discrete-time and have A and B matrices"
        )

        self.model = model_in_seconds
        self.A, self.B = sys.A, sys.B

        assert sys.A is not None and sys.B is not None, (
            "Model must have A and B matrices"
        )

        assert u_min_physical.shape == u_max_physical.shape, (
            "u_min and u_max must have the same shape"
        )

        self.nx = self.A.shape[0]
        self.nu = len(u_min_physical)
        self.nd = self.B.shape[1] - self.nu  # Modeled Disturbance dimension
        self.nd_gnd = 5
        self.ny = 5  # Tracked outputs (room temperatures)

        self.nx = self.A.shape[0]

        # Ground disturbance directions; same pattern as in build_augmented_system
        self.B_g = np.zeros((self.nx, self.nd_gnd))

        # NOTE: 5 Input disturbances to the LATENT states
        # self.B_g[self.nx // 2 :, :] = np.eye(self.nd_gnd)

        # NOTE: 5 Input disturbances to the ROOM AIR states
        self.B_g[: self.ny, :] = np.eye(self.nd_gnd)

        self.horizon = horizon

        # Scale bounds to normalized space
        self.u_min_W_m2 = u_min_physical
        self.u_max_W_m2 = u_max_physical
        self.u_min_W = NP_ROOM_AREAS * self.u_min_W_m2
        self.u_max_W = NP_ROOM_AREAS * self.u_max_W_m2
        self.u_min = scalers.heat.transform(self.u_min_W)
        self.u_max = scalers.heat.transform(self.u_max_W)
        self.u_zero = self.u_min  # Economic baseline

        self.margins = margins if margins is not None else np.zeros(5)

        # Split B into control and disturbance parts
        self.B_u = self.B[:, : self.nu]
        self.B_d = self.B[:, self.nu :]

        # Scale weights to account for different room sizes.
        # For energy efficiency, we care about energy per m2, not per room.
        # For comfort, (slack weights), we care about temperature violation per m2, not per room.
        self.effective_R_weights = (
            R_weights * scalers.heat.base_scaler.scale_ * (1.0 / NP_ROOM_AREAS)
        )
        # NOTE: remove the NP_ROOM_AREAS scaling for slack weights, since we want the penalty to be per degree of violation, not scaled by room area. This way, a 1 degree violation in a small room is penalized the same as a 1 degree violation in a large room, which makes more sense from a comfort perspective.
        self.effective_slack_weight = (
            slack_weights * scalers.temp.base_scaler.scale_  # * NP_ROOM_AREAS
        )
        assert self.effective_R_weights.shape == (self.nu,), (
            f"Effective R_weight must have same shape as inputs: ({self.nu},)"
        )

        assert self.effective_slack_weight.shape == (self.ny,), (
            f"Effective slack_weight must have same shape rooms: ({self.ny},)"
        )

        self.lambda_du = lambda_du

        self._setup_problem(
            R_weights=self.effective_R_weights,
            slack_weights=self.effective_slack_weight,
            lambda_du=self.lambda_du,
        )

    def _setup_problem(
        self, *, R_weights: ControlAction, slack_weights: SlackWeights, lambda_du: float
    ) -> None:
        """Initialize CVXPY variables, parameters, and problem."""
        # Decision variables
        self.x_var = cp.Variable((self.nx, self.horizon + 1))
        self.u_var = cp.Variable((self.nu, self.horizon))
        self.slack_lower = cp.Variable((self.ny, self.horizon))
        self.slack_upper = cp.Variable((self.ny, self.horizon))

        # Parameters (data provided at solve time)
        self.x_init = cp.Parameter(self.nx)
        self.d_forecast = cp.Parameter((self.nd, self.horizon))
        self.T_min_seq = cp.Parameter((self.ny, self.horizon))
        self.T_max_seq = cp.Parameter((self.ny, self.horizon))

        # scalar ground disturbance estimate (ground temperature offset)
        self.d_est_dyn = cp.Parameter(self.nd_gnd)

        # Build objective and constraints
        objective = self._build_objective(
            R_weights=R_weights, slack_weights=slack_weights, lambda_du=lambda_du
        )
        constraints = self._build_constraints()

        self.problem = cp.Problem(objective, constraints)

    @property
    def dt_in_seconds(self) -> float:
        return self.model.dt_in_seconds

    def _build_objective(
        self, *, R_weights: ControlAction, slack_weights: SlackWeights, lambda_du: float
    ) -> cp.Minimize:
        """Economic objective: minimize energy cost + constraint violation penalties."""

        ## Energy cost: R * (u - u_zero)
        cost = cp.sum(
            cp.multiply(self.u_var - self.u_zero[:, None], R_weights[:, None])
        )

        ## L1 comfort violation penalty
        cost += cp.sum(
            cp.multiply(self.slack_lower + self.slack_upper, slack_weights[:, None])
        )

        ## L2 comfort violation penalty
        # L2_weights = slack_weights * 100.0
        # cost += cp.sum(
        #     cp.multiply(
        #         cp.square(self.slack_lower) + cp.square(self.slack_upper),
        #         L2_weights[:, None],
        #     )
        # )

        # Differences along time axis: shape (nu, horizon-1)
        du = self.u_var[:, 1:] - self.u_var[:, :-1]
        # Sum of squared moves over horizon
        cost += lambda_du * cp.sum_squares(du)

        return cp.Minimize(cost)

    def _build_constraints(self) -> list[cp.Constraint]:
        constraints: list[cp.Constraint] = []

        # initial condition
        constraints.append(self.x_var[:, 0] == self.x_init)

        for k in range(self.horizon):
            # Dynamics
            constraints.append(
                self.x_var[:, k + 1]
                == self.A @ self.x_var[:, k]
                + self.B_u @ self.u_var[:, k]
                + self.B_d @ self.d_forecast[:, k]
                + self.B_g @ self.d_est_dyn
            )
            # Input Constraints
            constraints.extend(
                [
                    self.u_var[:, k] >= self.u_min,
                    self.u_var[:, k] <= self.u_max,
                ]
            )

            # x >= T_min - slack
            constraints.append(
                self.x_var[: self.ny, k + 1]  # + self.d_est
                >= self.T_min_seq[:, k] - self.slack_lower[:, k]
            )
            # x <= T_max + slack
            constraints.append(
                self.x_var[: self.ny, k + 1]  # + self.d_est
                <= self.T_max_seq[:, k] + self.slack_upper[:, k]
            )
            # Slacks must be positive
            constraints.extend(
                [self.slack_lower[:, k] >= 0, self.slack_upper[:, k] >= 0]
            )

        return constraints

    def _solve(
        self,
        *,
        x0: State,
        disturbance_forecast: DisturbanceForecast,
        Tmin_traj: TemperatureLimitTrajectory,
        Tmax_traj: TemperatureLimitTrajectory,
        debug: bool = False,
    ) -> ControlActionTrajectory:
        # NOTE: In order to be consistent with the bounded context in the solver, we assume different input shapes than the time-first convention used in the rest of the codebase. Therefore, we transpose inputs as needed when setting parameters.
        # This way the code better expresses the math.
        # BRIDGE IN: Transpose Time-First inputs to Features-First parameters
        # x0 is (nx,), so no transpose needed
        # This needs to be fixed in the future to avoid confusion, but for now we just need to be careful about shapes when setting parameters and when interpreting results.
        self.x_init.value = x0

        self.d_forecast.value = disturbance_forecast[: self.horizon, :].T

        self.T_min_seq.value = Tmin_traj[: self.horizon, :].T
        self.T_max_seq.value = Tmax_traj[: self.horizon, :].T

        self.d_est_dyn.value = self._d_est_dyn_scaled

        assert np.all(self.T_max_seq.value > self.T_min_seq.value), (
            "T_max must be greater than T_min for all time steps"
        )

        logger.debug(
            "x0[:]=%s  T_min_k1=%s  T_max_k1=%s disturbance_k0=%s",
            x0[:],
            Tmin_traj[0, :],
            Tmax_traj[0, :],
            disturbance_forecast[0, :],
        )

        # try:
        # ## for Quadratic problem
        # self.problem.solve(
        #     solver=cp.GUROBI,
        #     warm_start=True,
        #     verbose=False,
        #     Method=2,  # Use Barrier algorithm
        #     Crossover=0,  # Disable crossover
        #     FeasibilityTol=1e-4,
        #     OptimalityTol=1e-4,
        #     BarConvTol=1e-4,
        #     TimeLimit=10.0,  # E.g., 10 seconds
        # )
        ## for linear problem: remove L2 penalty
        # self.problem.solve(
        #     solver=cp.GUROBI,
        #     warm_start=True,
        #     verbose=False,
        #     Method=1,  # Dual Simplex (warm-startable)
        #     FeasibilityTol=1e-4,
        #     OptimalityTol=1e-4,
        #     TimeLimit=10.0,
        # )

        self.problem.solve(
            solver=cp.CLARABEL,
            warm_start=True,
            verbose=False,
            tol_gap_abs=1e-4,
            tol_gap_rel=1e-4,
            tol_feas=1e-4,
            time_limit=100.0,
        )

        BAD_STATUSES = {
            "infeasible",
            "unbounded",
            "infeasible_inaccurate",
            "unbounded_inaccurate",
        }

        if self.u_var.value is None or self.problem.status in BAD_STATUSES:
            raise MPCSolverError(
                f"Solver failed. Status: {self.problem.status}",
                status=self.problem.status,
            )

        logger.debug(
            "status=%s  cost=%.4f  u[:,0]=%s  predicted_x[:,1]=%s  slack_lo=%s  slack_hi=%s",
            self.problem.status,
            self.problem.value,
            self.u_var.value[:, 0],
            self.x_var.value[:, 1],
            self.slack_lower.value[:, 0],
            self.slack_upper.value[:, 0],
        )

        # NOTE: The controllers internal model is trained on normalized watts, so optimal control inputs should be in normalized units of power [W] (not flux [W/m2]).
        # The scaling back to physical units is done in the get_action method, after solving the MPC problem in normalized space.
        return self.u_var.value.T

    def get_action(
        self,
        *,
        current_state: np.ndarray,
        disturbance: DisturbanceForecast | None = None,
        reference: np.ndarray | None = None,
        room_temperature_soft_bounds: TemperatureBoundsTrajectory | None = None,
        d_est: np.ndarray | None = None,
        **kwargs,
    ) -> ControllerOutput:
        """Compute optimal control action (returns physical units).
        Args:
            current_state: Current state (x0) of the system (shape: (nx,))
            disturbance: Forecast of disturbances over the horizon (shape: (horizon, nd)) from k=0 to k=horizon-1, where each disturbance vector includes ambient temperature and solar radiation.
            reference: Desired reference trajectory for the outputs (not used in this controller) from k=1 (k=0 cannot be controlled) to k=horizon (shape: (horizon, ny))
            room_temperature_soft_bounds: Time-varying soft bounds for room temperatures over the horizon (shape: (horizon, ny, 2) from k=1 to k=horizon, where last dimension is [T_min, T_max])

        Returns:
            ControllerOutput containing the first control action in physical units (Watts per m2) and the full control trajectory for the horizon, as well as solver diagnostics.
        """

        if disturbance is None:
            raise ValueError("Disturbance must be provided for MPC controller")
        if room_temperature_soft_bounds is None:
            raise NotImplementedError(
                "State soft bounds must be provided for this controller"
            )
        if reference is not None:
            raise NotImplementedError(
                "Reference tracking is not implemented in this controller"
            )

        # Apply the safety margin buffer
        adjusted_bounds = room_temperature_soft_bounds.copy()
        # Increase T_min limit (e.g., 21.0 -> 21.5)
        adjusted_bounds[:, :, 0] += self.margins
        # Decrease T_max limit (e.g., 25.0 -> 24.5)
        adjusted_bounds[:, :, 1] -= self.margins

        # Scale inputs to normalized space using the tightened bounds
        scaled_x0 = self.scalers.temp.transform(current_state)

        scaled_d = self._scale_disturbances(disturbance)
        scaled_adjusted_bounds = self.scalers.temp.transform(adjusted_bounds)

        if d_est is None:
            self._d_est_dyn_scaled = np.zeros(self.nd)
        else:
            # d_est is (5,) °C → scale per component
            # self._d_est_dyn_scaled = self.scalers.temp.transform(d_est)
            self._d_est_dyn_scaled = d_est / self.scalers.temp.base_scaler.scale_

        scaled_Tmin_traj = scaled_adjusted_bounds[:, :, 0]
        scaled_Tmax_traj = scaled_adjusted_bounds[:, :, 1]

        # Solve in scaled space
        scaled_u_opt_Watts_norm = self._solve(
            x0=scaled_x0,
            disturbance_forecast=scaled_d,
            Tmin_traj=scaled_Tmin_traj,
            Tmax_traj=scaled_Tmax_traj,
            debug=self.debug,
        )

        # Scale back to physical units
        u_opt_Watts = self.scalers.heat.inverse_transform(scaled_u_opt_Watts_norm)

        u_opt_Watts_per_m2 = u_opt_Watts / NP_ROOM_AREAS

        return ControllerOutput(
            # Take only the first control action for receding horizon
            action=u_opt_Watts_per_m2[0, :],
            action_trajectory=u_opt_Watts_per_m2,  # Full control trajectory
            solver_status=self.problem.status,
            solve_time_sec=self.problem.solver_stats.solve_time
            if self.problem.solver_stats
            else None,
            solver_num_iters=self.problem.solver_stats.num_iters,
            solver_name=self.problem.solver_stats.solver_name
            if self.problem.solver_stats
            else None,
        )

    def _scale_disturbances(self, disturbance: DisturbanceForecast) -> np.ndarray:
        """Helper to scale disturbance forecast to normalized space."""
        tamb_norm = self.scalers.amb.transform(disturbance[:, 0])
        solar_norm = self.scalers.sol.transform(disturbance[:, 1])
        return np.column_stack([tamb_norm, solar_norm])[: self.horizon, :]

    def reset(self) -> None:
        pass
