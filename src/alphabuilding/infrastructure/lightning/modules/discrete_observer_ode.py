from typing import Callable, NamedTuple

import lightning as L
import numpy as np
import torch
import torch.nn as nn
from omegaconf import DictConfig
from torchmetrics.regression import (
    ExplainedVariance,
    MeanSquaredError,
    NormalizedRootMeanSquaredError,
)

from alphabuilding.domain.types import (
    GraphTopology,
    InitialStateEstimate,
    TrajectoryBatch,
)
from alphabuilding.infrastructure.pytorch.modules.dynamics_factory import (
    make_building_dynamics,
)
from alphabuilding.utils.paths import paths


class ModelOutput(NamedTuple):
    pred_zone_temps: torch.Tensor
    pred_hidden_states: torch.Tensor
    observer_traj: torch.Tensor | None
    target_temps: torch.Tensor
    observation_innovation_traj: torch.Tensor | None


# @torch.compile(fullgraph=True)
def exact_discretization(A, B, dt):
    """
    Computes exact ZOH discretization for dx/dt = Ax + Bu
    Returns Ad, Bd
    """
    n = A.shape[0]
    m = B.shape[1]

    # Construct augmented matrix M: [(n+m) x (n+m)]
    # [ A  B ]
    # [ 0  0 ]

    top_block = torch.cat([A, B], dim=1)  # Shape: [n, n+m]
    bottom_zeros = torch.zeros(m, n + m, device=A.device, dtype=A.dtype)

    M = torch.cat([top_block, bottom_zeros], dim=0)
    M_exp = torch.linalg.matrix_exp(M * dt)

    # Extract discrete matrices
    Ad = M_exp[:n, :n]
    Bd = M_exp[:n, n : n + m]

    return Ad, Bd


class DiscreteObserverGain(nn.Module):
    def __init__(self, num_outputs: int, num_states: int):
        super().__init__()
        self.num_outputs = num_outputs
        self.num_latent = num_states - num_outputs

        # Only the latent portion is learnable!
        if self.num_latent > 0:
            self.gain_latent = nn.Parameter(torch.zeros(self.num_latent, num_outputs))

    @property
    def gain(self):
        """Constructs the full K matrix [num_states, num_outputs]"""
        # Top block is Identity (we perfectly trust the sensor for observable states)
        K_meas = torch.eye(self.num_outputs, device=self.gain_latent.device)

        # Bottom block is the learned latent gain
        if self.num_latent > 0:
            return torch.cat([K_meas, self.gain_latent], dim=0)
        return K_meas


class LitMultiStepNeuralDiscreteODEModule(L.LightningModule):
    def __init__(
        self,
        optimizer: torch.optim.Optimizer,
        lr_scheduler: torch.optim.lr_scheduler,
        dynamics: DictConfig,
        horizon: int,
        window_size: int = 96,
        num_latent_states: int = 0,
        num_zones: int = 5,
        lr: float = 1e-3,
        weight_decay: float = 0,
        min_lr: float = 1e-6,
        topology: GraphTopology = GraphTopology.PHYSICAL_FULLY_CONNECTED,
        lambda_eigenvals_stability_penalty: float = 0.0,
        lambda_observer: float = 0.3,
    ):
        super().__init__()
        self.save_hyperparameters(logger=False, ignore=["dynamics"])
        self.num_zones = num_zones
        self.num_latent_states = num_latent_states

        topology = GraphTopology(topology)
        self.topology = topology
        if topology == GraphTopology.PHYSICAL_ONE_TO_ONE:
            assert num_latent_states == num_zones, (
                "1-to-1 topology requires num_latent_states to be equal to num_zones for a direct mapping between each zone and its corresponding latent state."
            )

        if num_latent_states > 0:
            self.num_states = num_zones + num_latent_states
        else:
            self.num_states = num_zones

        self.dynamics = make_building_dynamics(
            cfg=dynamics,
            num_zones=num_zones,
            num_latent_states=num_latent_states,
            topology=topology,
        )
        # self.dynamics = dynamics

        # Regularization weights
        assert lambda_eigenvals_stability_penalty >= 0.0, (
            "Stability penalty weight must be non-negative."
        )
        assert lambda_observer >= 0.0, "Observer loss weight must be non-negative."
        self.lambda_eigenvals_stability_penalty = lambda_eigenvals_stability_penalty
        self.lambda_observer = lambda_observer

        # Output matrix C: constant buffer that map states to measured outputs
        C = torch.zeros(self.num_zones, self.num_states, device=self.device)
        # C = [I | 0]
        C[range(self.num_zones), range(self.num_zones)] = 1
        self.register_buffer("C", C)

        # self.dynamics = base_dynamics_module
        self.horizon = horizon
        self.window_size = window_size
        self.lr = lr
        self.min_lr = min_lr

        self.vaf_metric = ExplainedVariance(multioutput="raw_values")
        self.nrmse = NormalizedRootMeanSquaredError(num_outputs=num_zones)
        self.test_rmse_celsius = MeanSquaredError(squared=False)
        self.test_rmse = MeanSquaredError(squared=False, num_outputs=self.num_zones)
        self.val_rmse_celsius = MeanSquaredError(squared=False)

        if num_latent_states > 0:
            self.observer = DiscreteObserverGain(self.num_zones, self.num_states)

    def _get_base_dynamics(self) -> nn.Module:
        return self.dynamics

    def _eigenvalue_stats(self):
        base_dynamics = self._get_base_dynamics()
        A = base_dynamics.A_matrix
        return self._compute_eigenvalue_stats(A)

    def _compute_eigenvalue_stats(self, A) -> tuple[torch.Tensor, torch.Tensor]:
        eigvals = torch.linalg.eigvals(A)
        real_eigvals = eigvals.real
        min_eig = torch.min(real_eigvals)
        max_eig = torch.max(real_eigvals)
        return min_eig, max_eig

    def _to_celsius(self, x: torch.Tensor) -> torch.Tensor:
        scaler = self.trainer.datamodule.zone_temp_scaler
        scale = torch.as_tensor(scaler.scale_, device=x.device, dtype=x.dtype)
        mean = torch.as_tensor(scaler.mean_, device=x.device, dtype=x.dtype)
        return x * scale.view(1, 1, -1) + mean.view(1, 1, -1)

    # @torch.compile()
    def _unroll_discrete(self, x0, u_traj, Ad, Bd, horizon):
        """
        Pure tensor recurrence loop. Ideal target for torch.compile.
        """
        # Pre-transpose for efficient matrix multiplication: x @ A.T
        Ad_T = Ad.T
        Bd_T = Bd.T

        x_curr = x0
        x_traj = [x0]

        # Use unbind to avoid slicing overhead in the loop.
        # faster when doing sequential access
        # input shape: [Batch, Time, Dim] -> tuple of [Batch, Dim]
        u_inputs = u_traj[:, :horizon, :].unbind(1)

        for u_t in u_inputs:
            x_next = x_curr @ Ad_T + u_t @ Bd_T
            x_traj.append(x_next)
            x_curr = x_next

        return torch.stack(x_traj, dim=1)  # Stack along time dim

    def forward_discrete(self, x0, u_traj, d_traj, dt):
        A = self.dynamics.A_matrix
        B = self.dynamics.B_matrix

        v = torch.cat((u_traj, d_traj), dim=2)[:, :-1, :]  # [B, Horizon, m]

        self.Ad, self.Bd = exact_discretization(A, B, dt)

        return self._unroll_discrete(x0, v, self.Ad, self.Bd, self.horizon)

    def forward(
        self,
        x0: torch.Tensor,
        dt: torch.Tensor,
        u: torch.Tensor,
        d: torch.Tensor,
    ) -> torch.Tensor:
        """Unrolls the discretized system for all inputs."""

        states_traj = self.forward_discrete(x0=x0, u_traj=u, d_traj=d, dt=dt)

        return states_traj

    def forward_observer_discrete(self, x0, u_traj, y_traj, dt):
        """
        Discrete-Time Current Observer (Filtered Form) Forward Pass.
        Args:
            x0: Initial guess [Batch, States]
            u_traj: Control/disturbance inputs [Batch, Time, U_Dim]
            y_traj: Measured outputs [Batch, Time, Y_Dim]
            dt: Sampling interval (scalar or tensor)
        Returns:
            observer_traj: [Batch, Time, States]
        """
        # Exact discretization of the OPEN-LOOP dynamics (without observer gain)
        A_c = self.dynamics.A_matrix
        B_c = self.dynamics.B_matrix
        Ad, Bd = exact_discretization(A_c, B_c, dt)

        # Pre-transpose for fast batch matrix multiplication
        Ad_T = Ad.T
        Bd_T = Bd.T
        K_T = self.observer.gain.T

        # NOTE: This is the first "estimate" -> initialized with the heuristic, so the "most" wrong.
        # it is the prior estimate at t=-W before seeing any measurements, so it won't be very good.
        # so the first "corrected" estimate will be at t=-W+1 after seeing the first measurement and input.
        x_curr = x0
        x_hat_traj = []
        innovation_traj = []

        # Unroll the discrete Current Observer
        # We unbind to iterate over time steps
        u_inputs = u_traj.unbind(1)
        y_meas = y_traj.unbind(1)

        # TODO: are inputs and measurements aligned in time?
        # or do we need to shift one of them by one step?
        for u_t, y_t in zip(u_inputs, y_meas):
            # Predict step (A priori)
            # x_{k|k-1} = Ad * x_{k-1|k-1} + Bd * u_{k-1}
            x_prior = (x_curr @ Ad_T) + (u_t @ Bd_T)  # [B, States]

            # Correct/Update step (A posteriori)
            # y_prior = C * x_{k|k-1} (assuming C extracts first num_zones)
            y_prior = x_prior[:, : self.num_zones]
            innovation = y_t - y_prior
            innovation_traj.append(innovation)

            # x_{k|k} = x_{k|k-1} + K * (y_k - y_prior)
            x_next = x_prior + (innovation @ K_T)

            x_hat_traj.append(x_next)
            x_curr = x_next

        return torch.stack(x_hat_traj, dim=1), torch.stack(innovation_traj, dim=1)

    # this method is also used for evalatuation
    def _estimate_initial_states(
        self, batch: TrajectoryBatch, batch_size: int | None = None
    ) -> InitialStateEstimate:
        most_recent_zone_temps = batch.past_zone_temps[:, -1, :]
        if self.num_latent_states > 0:
            past_zone_temps_traj = batch.past_zone_temps
            past_ambient_temp_traj = batch.past_ambient_temp
            past_heat_input_traj = batch.past_heat_inputs
            past_solar_rad_traj = batch.past_solar_rad

            # compute sampling_interval_in_hours from the data
            sampling_interval_in_ns = batch.past_timestamps[0, :2].diff().squeeze()
            # Convert nanoseconds to hours: 1 hour = 3600 seconds × 1e9 nanoseconds/second
            sampling_interval_in_hours = sampling_interval_in_ns / (3600 * 1e9)
            y_0 = past_zone_temps_traj[:, 0, :]  # [B, Zones] initial observed temps

            past_ambient_mean = past_ambient_temp_traj.mean(dim=(1))  # [B, 1, 1]
            past_zone_temps_mean = past_zone_temps_traj.mean(dim=(1))  # [B, Z]

            if self.num_latent_states != self.num_zones:
                # Initialize all latent states with the difference between mean
                # of zone temps and ambient temp
                all_zones_mean = past_zone_temps_mean.mean(dim=-1, keepdim=True)  # [B]
                global_mean = (all_zones_mean - past_ambient_mean) / 2.0
                # [B, 1]
                h_0 = global_mean.repeat(1, self.num_latent_states)
            elif self.num_latent_states == self.num_zones:
                h_0 = (past_zone_temps_mean + past_ambient_mean) / 2.0
            else:
                raise ValueError(
                    "something went wrong with latent state initialization"
                )

            x_0_observer = torch.cat(
                [
                    y_0,
                    h_0,
                ],
                dim=1,
            )

            # Unroll observer dynamics
            observer_traj, observer_innovation_traj = self.forward_observer_discrete(
                x0=x_0_observer,
                u_traj=torch.cat(
                    [past_heat_input_traj, past_ambient_temp_traj, past_solar_rad_traj],
                    dim=2,
                ),
                y_traj=past_zone_temps_traj,
                dt=sampling_interval_in_hours,
            )
            # [B, L+1, States] the +1 is because we return the initial condition x0 as well,
            # but its actually not interesting for our purposes

            # The estimate at t=0 is the last point of the observer (estimation) phase trajectory
            # running from t=-W to t=0
            x0_estimated = observer_traj[:, -1, :]  # [B, States]

            return InitialStateEstimate(
                x0=x0_estimated,
                observer_traj=observer_traj,
                innovation_traj=observer_innovation_traj,
            )
        else:
            return InitialStateEstimate(
                x0=most_recent_zone_temps, observer_traj=None, innovation_traj=None
            )

    # @torch.compile()
    def _run_forward_pass(self, batch: TrajectoryBatch) -> ModelOutput:
        """
        Pure data processing step.
        Extracts inputs, runs dynamics, and returns structured output.
        """

        # Initial State Estimation
        batch_size = batch.future_zone_temps.shape[0]
        if self.num_latent_states == 0:
            x0 = batch.past_zone_temps[:, -1, :]
            observer_traj = None
            observer_innovation_traj = None
        else:
            # a-posteriori estimate that updates the latent states based on
            # the innovation (y(0) - C x_prior) and the filtering observer gain.
            x0, observer_traj, observer_innovation_traj, _ = (
                self._estimate_initial_states(batch, batch_size=batch_size)
            )

        sampling_interval_in_ns = batch.past_timestamps[0, :2].diff().squeeze()
        sampling_interval_in_hours = sampling_interval_in_ns / (3600 * 1e9)

        u = batch.future_heat_inputs
        d = torch.cat(
            (batch.future_ambient_temp, batch.future_solar_rad),
            dim=2,
        )

        pred_states_traj = self.forward(x0=x0, dt=sampling_interval_in_hours, u=u, d=d)

        pred_zone_temps = pred_states_traj[:, :, : self.num_zones]
        pred_hidden = pred_states_traj[:, :, self.num_zones :]

        return ModelOutput(
            pred_zone_temps=pred_zone_temps,
            pred_hidden_states=pred_hidden,
            observer_traj=observer_traj,
            target_temps=batch.future_zone_temps,
            observation_innovation_traj=observer_innovation_traj,
        )

    def _compute_loss(self, output: ModelOutput, batch: TrajectoryBatch):
        """
        Pure loss computation step.
        """
        # Forecast MSE: Phase 2 - Open-Loop predictions (skip initial state t=0)
        forecast_mse = torch.nn.functional.mse_loss(
            output.pred_zone_temps[:, 1:, ...],
            output.target_temps[:, 1:, ...],
            reduction="mean",
        )

        total_loss = forecast_mse
        observer_mse = torch.tensor(0.0, device=self.device)

        # Observer innovation MSE (if applicable)
        if output.observation_innovation_traj is not None:
            observer_error = (output.observation_innovation_traj**2).mean()
            observer_mse = observer_error.mean()
            total_loss += self.lambda_observer * observer_mse

        return total_loss, {"forecast_mse": forecast_mse, "observer_mse": observer_mse}

    def _log_discrete_stability(self, dt):
        """
        Dedicated method for logging discrete eigenvalues.
        Calculates the SPECTRAL RADIUS (max abs eigenvalue).
        """
        # TODO: remove duplication
        with torch.no_grad():
            A = self.dynamics.A_matrix
            B = self.dynamics.B_matrix
            Ad, _ = exact_discretization(A, B, dt)

            eigvals_dyn = torch.linalg.eigvals(Ad)
            max_radius_dyn = torch.max(torch.abs(eigvals_dyn))
            discrete_min_eig, discrete_max_eig = self._compute_eigenvalue_stats(Ad)

            self.log(
                "dynamics/discrete_spectral_radius",
                max_radius_dyn,
                on_step=False,
                on_epoch=True,
            )
            self.log(
                "dynamics/discrete_max_real",
                torch.max(eigvals_dyn.real),
                on_step=False,
                on_epoch=True,
            )
            self.log(
                "dynamics/discrete_dynamics_eigenval_min",
                discrete_min_eig,
                on_step=False,
                on_epoch=True,
            )
            self.log(
                "dynamics/discrete_dynamics_eigenval_max",
                discrete_max_eig,
                on_step=False,
                on_epoch=True,
            )

            # Observer Stability (if applicable)
            if self.num_latent_states > 0:
                # observer error dynamics are e[k+1]=(I−KC)*Ad*e[k]
                # Build the (I - KC) operator
                I_minus_KC = torch.eye(
                    self.num_states, device=Ad.device, dtype=Ad.dtype
                )
                # K is shape [num_states, num_zones], C extracts first num_zones
                I_minus_KC[:, : self.num_zones] -= self.observer.gain

                # discrete closed-loop observer matrix
                Ad_obs = I_minus_KC @ Ad

                # Compute eigenvalues and log exactly as before
                discrete_observer_min_eig, discrete_observer_max_eig = (
                    self._compute_eigenvalue_stats(Ad_obs)
                )

                discrete_observer_min_eig, discrete_observer_max_eig = (
                    self._compute_eigenvalue_stats(Ad_obs)
                )

                self.log(
                    "observer/discrete_eigenval_min",
                    discrete_observer_min_eig,
                    on_step=False,
                    on_epoch=True,
                )
                self.log(
                    "observer/discrete_eigenval_max",
                    discrete_observer_max_eig,
                    on_step=False,
                    on_epoch=True,
                )

                eigvals_obs = torch.linalg.eigvals(Ad_obs)
                max_radius_obs = torch.max(torch.abs(eigvals_obs))

                self.log(
                    "observer/discrete_spectral_radius",
                    max_radius_obs,
                    on_step=False,
                    on_epoch=True,
                )
                self.log(
                    "observer/discrete_max_real",
                    torch.max(eigvals_obs.real),
                    on_step=False,
                    on_epoch=True,
                )

    def on_train_epoch_start(self):
        min_eig, max_eig = self._eigenvalue_stats()
        self.log(
            "dynamics/continuous_eigenval_min", min_eig, on_step=False, on_epoch=True
        )
        self.log(
            "dynamics/continuous_eigenval_max", max_eig, on_step=False, on_epoch=True
        )

    def on_train_epoch_end(self):
        # Log stability metrics ONCE at the end of the epoch
        if hasattr(self, "dt_hours"):
            self._log_discrete_stability(self.dt_hours)

            A_yh = self.dynamics.A_matrix[: self.num_zones, : self.num_zones]
            self.log("A_yh norm:", A_yh.norm().item(), on_step=False, on_epoch=True)

    def training_step(self, batch: TrajectoryBatch, batch_idx):
        # Update/Cache matrices. we only need to do this once per training step.
        # i.e. we unroll the dynamics using the same A and B matrices
        if hasattr(self.dynamics, "cache_matrices"):
            self.dynamics.cache_matrices()

        out = self._run_forward_pass(batch)
        loss, loss_components = self._compute_loss(out, batch)

        if hasattr(self.dynamics, "stability_penalty"):
            stability_penalty = self.dynamics.stability_penalty()
            self.log(
                "train/stability_penalty",
                stability_penalty,
                on_step=False,
                on_epoch=True,
            )

            weighted_stability_penalty = (
                self.lambda_eigenvals_stability_penalty * stability_penalty
            )
            self.log(
                "train/weighted_stability_penalty",
                weighted_stability_penalty,
                on_step=False,
                on_epoch=True,
            )
            loss += weighted_stability_penalty

        if self.num_latent_states > 0:
            grad_norm = (
                self.observer.gain_latent.grad.norm().item()
                if self.observer.gain_latent.grad is not None
                else 0.0
            )
            self.log(
                "observer/Kd_latent_grad_norm", grad_norm, on_step=False, on_epoch=True
            )

        self.log("train/loss", loss, prog_bar=True)
        self.log("train/forecast_mse", loss_components["forecast_mse"])
        self.log("train/observer_mse", loss_components["observer_mse"])

        # Logging (Diagnostics & Eigenvalues)
        # Cache dt_hours for epoch-end logging (only need to do this once)
        if not hasattr(self, "dt_hours"):
            sampling_interval_ns = batch.past_timestamps[0, :2].diff().squeeze()
            self.dt_hours = sampling_interval_ns / (3600 * 1e9)

        # if self.current_epoch % 5 == 0:
        #     # Extract a representative dt from this batch
        #     sampling_interval_ns = batch.past_timestamps[0, :2].diff().squeeze()
        #     dt_hours = sampling_interval_ns / (3600 * 1e9)
        #     self._log_discrete_stability(dt_hours)
        #     A_yh = self.dynamics.A_matrix[: self.num_zones, : self.num_zones]
        #     self.log("A_yh norm:", A_yh.norm().item(), on_step=False, on_epoch=True)

        return loss

    def validation_step(self, batch: TrajectoryBatch, batch_idx):
        out = self._run_forward_pass(batch)
        loss, loss_components = self._compute_loss(out, batch)

        preds = out.pred_zone_temps[:, 1:, :]
        targets = out.target_temps[:, 1:, :]

        preds_c = self._to_celsius(preds)
        targets_c = self._to_celsius(targets)

        self.val_rmse_celsius.update(preds_c.reshape(-1), targets_c.reshape(-1))

        error_celsius = preds_c - targets_c
        max_error_celsius = error_celsius.abs().max()

        self.log("val/loss", loss, prog_bar=True)
        self.log(
            "val/rmse_celsius",
            self.val_rmse_celsius,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
        )
        self.log(
            "val/max_error_celsius",
            max_error_celsius,
            on_step=False,
            on_epoch=True,
            reduce_fx="max",
        )
        self.log("val/forecast_mse", loss_components["forecast_mse"])
        self.log("val/observer_mse", loss_components["observer_mse"])

        return loss

    def predict_step(self, batch: TrajectoryBatch, batch_idx):
        out = self._run_forward_pass(batch)
        return self._future_traj_with_initial_step(
            batch, out.pred_zone_temps, out.pred_hidden_states
        )

    def on_validation_epoch_end(self):
        # VAF
        vaf_scores = self.vaf_metric.compute() * 100  # VAF = ExplainedVariance * 100
        for i in range(5):
            self.log(f"vaf/room_{i + 1}", vaf_scores[i])
        mean_vaf = torch.mean(vaf_scores)
        self.log("vaf/mean", mean_vaf)
        # Reset metric for the next epoch
        self.vaf_metric.reset()

        # FIT = (1 - NRMSE) * 100
        fit_values = (1.0 - self.nrmse.compute()) * 100
        self.log_dict({f"fit/room_{i + 1}": val for i, val in enumerate(fit_values)})
        self.log("fit/mean", torch.mean(fit_values))
        self.nrmse.reset()

    def test_step(self, batch, batch_idx):
        out = self._run_forward_pass(batch)

        # Skip t=0 (initial state)
        preds = out.pred_zone_temps[:, 1:, :]
        targets = out.target_temps[:, 1:, :]

        # Convert to Celsius (using the helper from the previous response)
        preds_c = self._to_celsius(preds)
        targets_c = self._to_celsius(targets)

        # Flatten time and batch dimensions: [B, T, Z] -> [B*T, Z]
        preds_c_flat = preds_c.reshape(-1, self.num_zones)
        targets_c_flat = targets_c.reshape(-1, self.num_zones)

        # Accumulate errors per zone
        self.test_rmse.update(preds_c_flat, targets_c_flat)

        return out._asdict()

    def on_test_epoch_end(self):
        # Returns a tensor of shape [num_zones] containing the RMSE for each zone
        rmse_per_zone = self.test_rmse.compute()

        # Log the RMSE for each individual room
        log_dict = {}
        for i, rmse_val in enumerate(rmse_per_zone):
            log_dict[f"test/rmse_celsius_room_{i + 1}"] = rmse_val

        # Log the mean of the zone RMSEs
        log_dict["test/rmse_celsius_mean"] = torch.mean(rmse_per_zone)

        # log_dict automatically handles multiple metrics
        self.log_dict(log_dict)

        # Reset for future test runs
        self.test_rmse.reset()

    def configure_optimizers(self):
        param_groups = self.parameters()
        # Create optimizer with parameter groups
        optimizer = self.hparams.optimizer(
            param_groups, lr=self.hparams.lr, weight_decay=self.hparams.weight_decay
        )
        scheduler = self.hparams.lr_scheduler(optimizer=optimizer)

        lr_scheduler_config = {
            "scheduler": scheduler,
            "interval": "epoch",
            "frequency": 1,
        }

        if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
            lr_scheduler_config["monitor"] = "val/loss"

        return {
            "optimizer": optimizer,
            "lr_scheduler": lr_scheduler_config,
        }

    def _future_traj_with_initial_step(
        self,
        batch: TrajectoryBatch,
        pred_zone_temp_traj: torch.Tensor,
        pred_hidden_states_traj: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        # Why 0 index at the first dimension? Select single batch
        return {
            "preds": pred_zone_temp_traj.squeeze(1),  # [L+1, Z]
            "target_temps": batch.future_zone_temps[0, :, :],  # [L+1, Z]
            "ambient_temps": batch.future_ambient_temp[0, :, :],  # [L+1, 1]
            "heat_inputs": batch.future_heat_inputs[0, :, :],  # [L+1, Z]
            "timestamps": batch.future_timestamps[0, : self.horizon + 1],  # [L+1, 1]
            "hidden_states": pred_hidden_states_traj.squeeze(1),  # [L+1, H]
            "solar_radiation": batch.future_solar_rad[0, :, :],  # [L+1, 1]
        }
