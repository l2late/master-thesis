from typing import Protocol, runtime_checkable

import numpy as np

from alphabuilding.constants import ROOM_AREAS
from alphabuilding.control.types import (
    ControlAction,
    InputMatrix,
    ObserverGain,
    ObserverInput,
    Output,
    OutputMatrix,
    State,
    SystemMatrix,
)
from alphabuilding.domain.types import Scalers


@runtime_checkable
class StateEstimator(Protocol):
    """Protocol for state estimation algorithms."""

    @property
    def x_hat(self) -> State:
        """Return the current state estimate."""
        ...

    def update(self, u_prev: ControlAction, y_current: Output) -> State:
        """
        Update the state estimate based on the control action applied
        in the PREVIOUS step and the measurement observed in the CURRENT step.

        Args:
            u: Control action applied at step k-1 (shape: nu,)
            y: Measurement observed at step k (shape: ny,)

        Returns:
            The updated state estimate x_hat[k|k] (shape: nx,)
        """
        ...

    def reset(self, x0: State) -> None:
        """Reset the internal state estimate to x0."""
        ...


class FilteringLuenbergerObserver(StateEstimator):
    """
    Standard discrete, filtering (current) Luenberger observer.
    Computes x_hat(k|k) using the previous control input u(k-1) and the current measurement y(k).

    Diagnostic properties are split by estimation stage:
        - Prior  (k|k-1): after predict step, before correction
        - Posterior (k|k): after correction step

    Output errors and state errors are available in physical units.
    State errors require x_true to be passed into update(), which is only
    possible in simulation. In deployment, they return NaN.
    """

    def __init__(
        self,
        *,
        Ad: SystemMatrix,
        Bd: InputMatrix,
        C: OutputMatrix,
        Kd: ObserverGain,
        x0: State,
        scalers: Scalers,
    ):
        """
        Discrete-time Luenberger Observer in predict-correct form.
        Predict: x_hat(k|k-1) = A * x_hat(k-1|k-1) + B * u(k-1)
        Correct: x_hat(k|k) = x_hat(k|k-1) + K * innovation(k)
        where the innovation is: innovation(k) = y(k) - C * x_hat(k|k-1)
        """
        self.A = Ad
        self.B = Bd
        self.C = C
        self.K = Kd
        self.nx = Ad.shape[0]
        self.ny = C.shape[0]
        assert Kd.shape == (self.nx, self.ny), f"Gain K shape mismatch: {Kd.shape}"
        self.scalers = scalers

        self._reset(x0)

        assert self.is_stable(), (
            "Observer is not stable. Check eigenvalues of (I - KC)A."
        )

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    @property
    def x_hat(self) -> State:
        """Posterior state estimate x_hat(k|k) in physical units."""
        return self._x_hat_unscaled.copy()

    def update(
        self,
        u_prev: ObserverInput,
        y_current: Output,
        x_true: State | None = None,
    ) -> State:
        """
        Update the state estimate.

        Args:
            u_prev:   u(k-1) control/disturbance input applied at step k-1.
            y_current: y(k) measurement observed at step k.
            x_true:   (optional) true plant state x(k), only available in simulation.
                      When provided, prior_state_error and posterior_state_error
                      are populated. Otherwise they return NaN.

        Returns:
            x_hat(k|k) in physical units.
        """
        # --- Scale inputs ---
        heat_W_per_m2 = u_prev[:5]
        heat_W_scaled = self.scalers.heat.transform(
            heat_W_per_m2 * np.array(ROOM_AREAS)
        )
        amb_scaled = self.scalers.amb.transform(u_prev[5])
        sol_rad_scaled = self.scalers.sol.transform(u_prev[6])
        u_scaled = np.concatenate([heat_W_scaled, [amb_scaled], [sol_rad_scaled]])

        self._y_current_unscaled = y_current.copy()
        self._x_true = (
            x_true.astype(float) if x_true is not None else np.full(self.nx, np.nan)
        )
        y_scaled = self.scalers.temp.transform(y_current)

        # --- STEP 1: Predict (prior) ---
        # x_hat(k|k-1) = A * x_hat(k-1|k-1) + B * u(k-1)
        self._x_hat_prior_scaled = self.A @ self._x_hat_scaled + self.B @ u_scaled
        self._x_hat_prior_unscaled = self.scalers.temp.inverse_transform(
            self._x_hat_prior_scaled
        )

        # --- STEP 2: Innovation ---
        # e(k) = y(k) - C * x_hat(k|k-1)
        self._innovation_scaled = y_scaled - self.C @ self._x_hat_prior_scaled

        # --- STEP 3: Correct (posterior) ---
        # x_hat(k|k) = x_hat(k|k-1) + K * e(k)
        self._x_hat_scaled = self._x_hat_prior_scaled + self.K @ self._innovation_scaled
        self._x_hat_unscaled = self.scalers.temp.inverse_transform(self._x_hat_scaled)

        return self._x_hat_unscaled.copy()

    # ------------------------------------------------------------------
    # Output error diagnostics  (physical units, °C)
    # Convention: error = true - predicted  (positive = underestimate)
    # ------------------------------------------------------------------

    @property
    def prior_output_error(self) -> Output:
        """
        Innovation / prior output prediction error in physical units (°C).

            e_prior(k) = y(k) - C @ x_hat(k|k-1)

        Positive  → observer underestimates the output before correction.
        Persistent non-zero values indicate model mismatch or a poorly tuned gain K.
        NaN before the first update() call.
        """
        if np.any(np.isnan(self._y_current_unscaled)):
            return np.full(self.ny, np.nan)
        y_prior_pred = self.scalers.temp.inverse_transform(
            self.C @ self._x_hat_prior_scaled
        )
        return self._y_current_unscaled - y_prior_pred

    @property
    def posterior_output_error(self) -> Output:
        """
        Posterior output prediction error in physical units (°C).

            e_post(k) = y(k) - C @ x_hat(k|k)

        Measures how much residual output error remains after correction.
        Ideally small; persistent bias here means K is over- or under-correcting.
        NaN before the first update() call.
        """
        if np.any(np.isnan(self._y_current_unscaled)):
            return np.full(self.ny, np.nan)
        y_post_pred = self.scalers.temp.inverse_transform(self.C @ self._x_hat_scaled)

        return self._y_current_unscaled - y_post_pred

    @property
    def scaled_innovation(self) -> Output:
        """Prior output error in scaled space. Equivalent to prior_output_error but normalized."""
        return self._innovation_scaled.copy()

    # ------------------------------------------------------------------
    # State error diagnostics  (physical units, °C)
    # Only meaningful in simulation where x_true is available via update().
    # Convention: error = x_true - x_hat  (positive = underestimate)
    # ------------------------------------------------------------------

    @property
    def prior_state_error(self) -> State:
        """
        Prior state estimation error in physical units (°C).

            eps_prior(k) = x(k) - x_hat(k|k-1)

        Positive → observer underestimates the true state before correction.
        NaN if x_true was not passed to update() (i.e., in deployment).
        """
        return self._x_true - self._x_hat_prior_unscaled

    @property
    def posterior_state_error(self) -> State:
        """
        Posterior state estimation error in physical units (°C).

            eps_post(k) = x(k) - x_hat(k|k)

        This is the error seen by the MPC at each control step.
        Positive → observer underestimates the true state after correction,
                   MPC thinks it's colder than reality → may overheat.
        Negative → observer overestimates → MPC thinks it's warmer than reality
                   → may underheat → comfort lower-bound violations.
        NaN if x_true was not passed to update() (i.e., in deployment).
        """
        return self._x_true - self._x_hat_unscaled

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _reset(self, x0: State) -> None:
        self._x_hat_unscaled = x0.astype(float)
        self._x_hat_scaled = self.scalers.temp.transform(x0)
        self._x_hat_prior_scaled = self._x_hat_scaled.copy()
        self._x_hat_prior_unscaled = x0.astype(float)
        self._innovation_scaled = np.zeros(self.ny)
        self._y_current_unscaled = np.full(self.ny, np.nan)
        self._x_true = np.full(self.nx, np.nan)

    def reset(self, x0: State) -> None:
        """Reset the observer to a known initial state."""
        self._reset(x0)

    def is_stable(self) -> np.bool_:
        """
        Check observer stability.
        The error dynamics for a discrete filtering observer are:
            e(k) = (I - KC) * A * e(k-1)
        Stability requires all eigenvalues of (I - KC)A inside the unit circle.
        """
        I_minus_KC = np.eye(self.nx) - self.K @ self.C
        A_obs = I_minus_KC @ self.A
        eigvals = np.linalg.eigvals(A_obs)
        return np.all(np.abs(eigvals) < 1)


def build_augmented_system(A, B, C, nd):
    nx = A.shape[0]
    ny = C.shape[0]

    # ground disturbances only affect latent (last 5) states, one per zone
    B_d_aug = np.zeros((nx, nd))
    # shape (5 latent states x 5 disturbances) ~ diagonal or full, you can choose

    # NOTE: Each LATENT state j gets its own d_j
    # B_d_aug[nx // 2 :, :] = np.eye(nd)

    # NOTE: Each ROOM AIR state j gets its own d_j
    B_d_aug[:ny, :] = np.eye(nd)

    A_aug = np.block(
        [
            [A, B_d_aug],  # (nx x nx+1)
            [np.zeros((nd, nx)), np.eye(nd)],  # integrator row
        ]
    )
    B_aug = np.vstack([B, np.zeros((nd, B.shape[1]))])
    C_aug = np.hstack([C, np.zeros((ny, nd))])  # D_d = 0
    return A_aug, B_aug, C_aug


def check_observability(A, C, tol=1e-10):
    nx = A.shape[0]
    O = np.vstack([C @ np.linalg.matrix_power(A, k) for k in range(nx)])
    rank = np.linalg.matrix_rank(O, tol=tol)
    return rank, nx, rank == nx


def check_detectability_pbh(A, C, tol=1e-8):
    """For each eigenvalue |λ| >= 1, check rank([λI-A; C]) == nx."""
    nx = A.shape[0]
    eigvals = np.linalg.eigvals(A)
    undetectable = []
    for lam in eigvals:
        if np.abs(lam) >= 1.0 - tol:
            M = np.vstack([lam * np.eye(nx) - A, C])
            if np.linalg.matrix_rank(M, tol=tol) < nx:
                undetectable.append(lam)

    return undetectable


def conditioning_report(A_aug, C_aug, nd, tol=1e-10):
    n_aug = A_aug.shape[0]

    O = np.vstack([C_aug @ np.linalg.matrix_power(A_aug, k) for k in range(n_aug)])
    svd_O = np.linalg.svd(O, compute_uv=False)
    cond_O = svd_O[0] / svd_O[-1]

    W = O.T @ O
    eigvals_W = np.sort(np.linalg.eigvalsh(W))[::-1]
    cond_W = eigvals_W[0] / eigvals_W[-1] if eigvals_W[-1] > tol else np.inf

    svd_A = np.linalg.svd(A_aug, compute_uv=False)
    cond_A = svd_A[0] / svd_A[-1]

    O_x = O[:, :-nd]
    O_d = O[:, -nd:]
    svd_Ox = np.linalg.svd(O_x, compute_uv=False)
    svd_Od = np.linalg.svd(O_d, compute_uv=False)

    print(f"cond(O)  : {cond_O:.4e}  {'✓' if cond_O < 1e6 else '⚠ ill-conditioned'}")
    print(
        f"cond(W)  : {cond_W:.4e}  {'✓' if cond_W < 1e10 else '⚠  Riccati may struggle'}"
    )
    print(f"cond(A)  : {cond_A:.4e}")
    print(f"σ_min(O_x): {svd_Ox[-1]:.4e}  (original states)")
    print(f"σ_min(O_d): {svd_Od[-1]:.4e}  (disturbance block)")
    ratio = svd_Ox[-1] / svd_Od[-1]
    print(
        f"σ ratio x/d: {ratio:.4e}  {'⚠ scale Q_d separately' if ratio < 1e-3 or ratio > 1e3 else '✓ balanced'}"
    )


from scipy.linalg import solve_discrete_are


def design_augmented_gain(A_aug, C_aug, nx, nd, qx=1e-4, qd=1e-2, ry=1e-8):
    """
    Design an augmented observer gain K_aug for z = [x; d].

    qx: process noise level for physical states x
    qd: process noise level for disturbance states d
    ry: measurement noise level (very small since simulator is noise-free)
    """
    n_aug = A_aug.shape[0]
    ny = C_aug.shape[0]

    Q = np.zeros((n_aug, n_aug))
    Q[:nx, :nx] = qx * np.eye(nx)
    Q[nx:, nx:] = qd * np.eye(nd)
    R = ry * np.eye(ny)

    # Solve discrete-time Riccati
    P = solve_discrete_are(A_aug.T, C_aug.T, Q, R)

    # Steady-state Kalman gain
    K_aug = P @ C_aug.T @ np.linalg.inv(C_aug @ P @ C_aug.T + R)
    return K_aug, Q, R


class AugmentedLuenbergerObserver(StateEstimator):
    def __init__(
        self,
        *,
        A_aug: SystemMatrix,
        B_aug: InputMatrix,
        C_aug: OutputMatrix,
        K_aug: ObserverGain,
        nx: int,
        nd: int,
        x0: State,
        scalers: Scalers,
    ):
        self.A = A_aug
        self.B = B_aug
        self.C = C_aug
        self.K = K_aug
        self.nx = nx
        self.nd = nd
        self.n_aug = nx + nd
        self.ny = C_aug.shape[0]
        assert K_aug.shape == (self.n_aug, self.ny)
        self.scalers = scalers
        self._reset(x0)

    @property
    def x_hat(self) -> State:
        # first nx components
        return self._z_hat_unscaled[: self.nx].copy()

    @property
    def d_hat(self) -> Output:
        # last nd components
        return self._z_hat_unscaled[self.nx : self.nx + self.nd].copy()

    def update(
        self,
        u_prev: ObserverInput,
        y_current: Output,
        x_true: State | None = None,
    ) -> State:
        heat_W_per_m2 = u_prev[:5]
        heat_W_scaled = self.scalers.heat.transform(
            heat_W_per_m2 * np.array(ROOM_AREAS)
        )
        amb_scaled = self.scalers.amb.transform(u_prev[5])
        sol_scaled = self.scalers.sol.transform(u_prev[6])
        u_scaled = np.concatenate([heat_W_scaled, [amb_scaled], [sol_scaled]])

        self._y_current_unscaled = y_current.copy()
        self._x_true = (
            x_true.astype(float) if x_true is not None else np.full(self.nx, np.nan)
        )

        y_scaled = self.scalers.temp.transform(y_current)

        # --- STEP 1: Predict (prior) ---
        self._z_hat_prior_scaled = self.A @ self._z_hat_scaled + self.B @ u_scaled
        self._z_hat_prior_unscaled = self.scalers.temp.inverse_transform(
            self._z_hat_prior_scaled[: self.nx]
        )

        # --- STEP 2: Innovation ---
        self._innovation_scaled = y_scaled - self.C @ self._z_hat_prior_scaled

        # --- STEP 3: Correct (posterior) ---
        self._z_hat_scaled = self._z_hat_prior_scaled + self.K @ self._innovation_scaled

        # unpack: first nx states use temp scaler, last nd are also temps
        x_scaled = self._z_hat_scaled[: self.nx]
        d_scaled = self._z_hat_scaled[self.nx : self.nx + self.nd]
        x_unscaled = self.scalers.temp.inverse_transform(x_scaled)
        d_unscaled = d_scaled * self.scalers.temp.base_scaler.scale_
        self._z_hat_unscaled = np.concatenate([x_unscaled, d_unscaled])

        return x_unscaled.copy()

    def _reset(self, x0: State) -> None:
        # start with zero disturbance
        z0_unscaled = np.concatenate([x0.astype(float), np.zeros(self.nd)])
        # scale both x and d with the temp scaler
        z0_scaled = self.scalers.temp.transform(z0_unscaled)
        self._z_hat_unscaled = z0_unscaled
        self._z_hat_scaled = z0_scaled
        self._z_hat_prior_scaled = z0_scaled.copy()
        self._z_hat_prior_unscaled = x0.astype(float)
        self._innovation_scaled = np.zeros(self.ny)
        self._y_current_unscaled = np.full(self.ny, np.nan)
        self._x_true = np.full(self.nx, np.nan)

    def reset(self, x0: State) -> None:
        self._reset(x0)

    # Output error diagnostics (physical units, °C)
    @property
    def prior_output_error(self) -> Output:
        """
        Innovation / prior output prediction error in physical units (°C).
        e_prior(k) = y(k) - C @ z_hat(k|k-1)
        """
        if np.any(np.isnan(self._y_current_unscaled)):
            return np.full(self.ny, np.nan)
        # C @ z_hat_prior_scaled is in scaled space → inverse_transform
        y_prior_pred = self.scalers.temp.inverse_transform(
            self.C @ self._z_hat_prior_scaled
        )
        return self._y_current_unscaled - y_prior_pred

    @property
    def posterior_output_error(self) -> Output:
        """
        Posterior output prediction error in physical units (°C).
        e_post(k) = y(k) - C @ z_hat(k|k)
        """
        if np.any(np.isnan(self._y_current_unscaled)):
            return np.full(self.ny, np.nan)
        y_post_pred = self.scalers.temp.inverse_transform(self.C @ self._z_hat_scaled)
        return self._y_current_unscaled - y_post_pred
