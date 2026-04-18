import matplotlib.pyplot as plt
import numpy as np
import torch

from utils.instantiation import (
    get_last_module_and_datamodule_from_checkpoint,
)
from utils.state_space import (
    diagnose_continuous_system,
    discretize_system,
    get_continuous_A_B_C_D_from_dynamics_module,
)
from analysis.plot_system_matrices import plot_A_and_B_matrices

module, datamodule = get_last_module_and_datamodule_from_checkpoint(
    auto_select_last=True
)

A_cont, B_cont, C, D = get_continuous_A_B_C_D_from_dynamics_module(module.dynamics)

dt_hours = 0.25  # 15 minutes in hours
diagnose_continuous_system(A_cont, B_cont, dt_hours)
A_disc, B_disc = discretize_system(A_cont, B_cont, C, dt_hours=dt_hours)

# Plot continuous and discretized A and B matrices
plot_A_and_B_matrices(A_cont, B_cont)
plot_A_and_B_matrices(A_disc, B_disc)


def create_reference_trajectory(current_time_hours, horizon_steps, dt, n_zones=5):
    """Reference for all zones (same setpoint).
    Creates reference temperature trajectory.
    16°C: 00:00-08:00 and 18:00-24:00
    20°C: 08:00-18:00
    """
    ref = np.zeros((horizon_steps, n_zones))

    for i in range(horizon_steps):
        time_hour = (current_time_hours + i * dt) % 24
        temp = 28.0 if (8 <= time_hour < 18) else 22
        ref[i, :] = temp  # Vector for all 5 zones

    return ref


def simulate(simulation_steps=96):
    current_time = 0.0  # Start at midnight

    # Storage for plotting
    controls_history_scaled = []
    references_history = []

    datamodule.setup("test")
    test_dataloader = datamodule.test_dataloader()
    test_iterator = iter(test_dataloader)
    temperature_scaler = datamodule.zone_temp_scaler

    batch = next(test_iterator)
    # 1. Get initial state estimate
    with torch.no_grad():
        x_hat_normalized = (
            module._get_initial_states(batch, batch_size=1)
            .squeeze(0)
            .detach()
            .cpu()
            .numpy()
        )
    x_zones_normalized = x_hat_normalized[:5]
    x_hidden_normalized = x_hat_normalized[5:]

    # Storage for plotting
    normalized_states_history = [x_hat_normalized]

    for step in range(simulation_steps):
        # 2. Create reference trajectory
        y_ref = create_reference_trajectory(current_time, N, dt_hours)
        y_ref_shape = y_ref.shape
        y_ref = y_ref.reshape(-1, 1)
        y_ref_normalized = temperature_scaler.transform(y_ref)
        y_ref_normalized = y_ref_normalized.reshape(y_ref_shape)
        references_history.append(y_ref_normalized[0])

        # 3. Get ambient temperature forecast
        d_ambient_forecast_normalized = (
            batch["future_ambient_temp_traj"][0, :, 0].squeeze(0).cpu().numpy()
        )
        d_ambient_forecast_denormalized = temperature_scaler.inverse_transform(
            d_ambient_forecast_normalized.reshape(-1, 1)
        ).squeeze()

        u = batch["future_heat_input_traj"][0, :, 0].squeeze(0).cpu().numpy()
        augmented_inputs = np.concatenate((u, d_ambient_forecast_normalized), axis=0)

        x_next = A_disc @ x_hat_normalized + B_disc @ augmented_inputs
        normalized_states_history.append(x_next)

        current_time += dt_hours
        current_time = current_time % 24  # Wrap around day

    return (
        np.array(normalized_states_history),
        np.array(controls_history_scaled),
        np.array(references_history),
    )


if __name__ == "__main__":
    N = 24  # horizon
    simulation_steps = 48
    # TODO: check scaling is right for Q and R
    # and elsewere in the mpc optimization
    u_min_normalized = np.array([0.0])  # Minimum radiator power
    u_max_normalized = np.array([1])  # Maximum radiator power (W)

    x, u, r = simulate(simulation_steps)  # 2 days

    temperature_scaler = datamodule.zone_temp_scaler
    heat_input_scaler = datamodule.heat_input_scaler
    x = temperature_scaler.inverse_transform(x.reshape(-1, x.shape[1])).reshape(x.shape)
    r = temperature_scaler.inverse_transform(r.reshape(-1, r.shape[1])).reshape(r.shape)
    u = heat_input_scaler.inverse_transform(u.reshape(-1, u.shape[1])).reshape(u.shape)
    u_max_denormalized = heat_input_scaler.inverse_transform(
        u_max_normalized.reshape(-1, 1)
    ).reshape(u_max_normalized.shape)

    # %%
    import matplotlib.pyplot as plt

    time_axis = np.arange(x.shape[0]) * dt_hours
    n_zones = 5  # First 5 states are zone temperatures

    fig, axes = plt.subplots(n_zones, 1, figsize=(14, 10), sharex=True)

    colors = ["C0", "C1", "C2", "C3", "C4"]

    t_max = x[:, :n_zones].max()
    r_max = r.max()
    for i in range(n_zones):
        ax1 = axes[i]

        # Plot temperature on left y-axis
        ax1.plot(
            time_axis,
            x[:, i],
            color=colors[i],
            linewidth=2,
            label=f"Zone {i + 1} Temp",
        )
        ax1.plot(
            time_axis[:-1],
            r[:, i],
            "--",
            color=colors[i],
            alpha=0.7,
            linewidth=1.5,
            label=f"Zone {i + 1} Ref",
        )

        ax1.set_ylabel("Temp (°C)", fontsize=11)
        ax1.legend(loc="upper left", fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim([0, time_axis[-1]])
        ax1.set_ylim([0, t_max * 1.1])

        # Plot control input on right y-axis
        ax2 = ax1.twinx()
        ax2.step(
            time_axis[:-1],
            u[:, 0],
            where="post",
            color="black",
            linewidth=1.5,
            alpha=0.6,
            label="Control",
        )
        ax2.set_ylabel("Power (W)", fontsize=11, color="black")
        ax2.tick_params(axis="y", labelcolor="black")
        ax2.set_ylim([0, u_max_denormalized.max() * 1.1])
        ax2.legend(loc="upper right", fontsize=9)

    # Only set xlabel on bottom subplot
    axes[-1].set_xlabel("Time (hours)", fontsize=12)

    # Add overall title
    fig.suptitle(
        "MPC Closed-Loop Control: Zone Temperatures and Control Input",
        fontsize=14,
        y=0.995,
    )

    plt.tight_layout()
    plt.show()

    # %%
    # Optional: Plot tracking error for each zone
    fig, axes = plt.subplots(n_zones, 1, figsize=(12, 10), sharex=True)

    for i in range(n_zones):
        tracking_error = x[:-1, i] - r[:, i]
        axes[i].plot(time_axis[:-1], tracking_error, color=colors[i], linewidth=2)
        axes[i].axhline(0, color="k", linestyle="--", alpha=0.3)
        axes[i].set_ylabel(f"Zone {i + 1}\nError (°C)", fontsize=10)
        axes[i].grid(True, alpha=0.3)

        # Add statistics
        mae = np.mean(np.abs(tracking_error))
        rmse = np.sqrt(np.mean(tracking_error**2))
        axes[i].text(
            0.02,
            0.95,
            f"MAE: {mae:.2f}°C\nRMSE: {rmse:.2f}°C",
            transform=axes[i].transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            fontsize=8,
        )
        # fix 0 in middle of y-axis
        y_lim = max(abs(tracking_error.min()), abs(tracking_error.max())) * 1.1
        axes[i].set_ylim([-y_lim, y_lim])

    axes[-1].set_xlabel("Time (hours)", fontsize=12)
    fig.suptitle("Temperature Tracking Errors by Zone", fontsize=14)
    plt.tight_layout()
    plt.show()
    print("Done")

    # %%
    # Optional: Plot all hidden states (beyond zone temps)
    # if x.shape[1] > n_zones:
    #     n_hidden = x.shape[1] - n_zones
    #     n_cols = min(3, n_hidden)
    #     n_rows = int(np.ceil(n_hidden / n_cols))
    #
    #     fig, axes = plt.subplots(
    #         n_rows, n_cols, figsize=(15, 3 * n_rows), squeeze=False
    #     )
    #
    #     for idx in range(n_hidden):
    #         row = idx // n_cols
    #         col = idx % n_cols
    #         axes[row, col].plot(time_axis, x[:, n_zones + idx], linewidth=2)
    #         axes[row, col].set_ylabel(f"State {n_zones + idx + 1}", fontsize=10)
    #         axes[row, col].grid(True, alpha=0.3)
    #         axes[row, col].set_xlabel("Time (hours)", fontsize=10)
    #
    #     # Hide unused subplots
    #     for idx in range(n_hidden, n_rows * n_cols):
    #         row = idx // n_cols
    #         col = idx % n_cols
    #         axes[row, col].axis("off")
    #
    #     fig.suptitle("Hidden States (Thermal Mass)", fontsize=14)
    #     plt.tight_layout()
    #     plt.show()
