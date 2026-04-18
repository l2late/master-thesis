from collections import defaultdict
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import torch
from lightning import LightningDataModule


def _plot_all_rooms_targets_and_ambient(data: dict[str, np.ndarray]) -> None:
    # Unpack data
    timestamps = data["timestamps"]
    targets = data["targets"]
    ambient_temps = data["ambient_temps"]
    heat_inputs = data["heat_inputs"]

    n_timesteps, n_rooms = targets.shape

    # %%
    fig, axs = plt.subplots(n_rooms, 1, figsize=(10, 2 * n_rooms), sharex=True)

    for i in range(n_rooms):
        ax = axs[i]
        ax.plot(timestamps, targets[:, i], label="Target", color="orange")
        ax.plot(timestamps, ambient_temps[:], label="Ambient ", color="green")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title(f"Room {i + 1}")
        ax.legend()
        ax.grid()
        ax.legend(loc="upper right")

        # Add secondary y-axis for heat input
        ax2 = ax.twinx()
        ax2.plot(
            timestamps,
            heat_inputs[:, i],
            label="Heat Input",
            color="red",
            linestyle="--",
        )
        ax2.set_ylabel("Heat Input", color="red")
        ax2.tick_params(axis="y", labelcolor="red")

        # Combine legends from both axes
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()

    # date_format = mdates.DateFormatter("%Y-%m-%d %H:%M")
    date_format = mdates.DateFormatter("%b %d, %H:%M")
    axs[-1].xaxis.set_major_formatter(date_format)

    # --- 4. Auto-rotate date labels for better readability ---
    fig.autofmt_xdate()
    plt.suptitle(
        f"Direct Time Stepping Predictions for {n_timesteps} Timesteps",
    )
    plt.tight_layout()  # Adjust layout for external legend
    # plt.show()
    print("Plotting completed for all rooms' targets and ambient temperatures.")


import numpy as np


def _safe_step_ylim(y, *, bottom=None, top=None, pad_frac=0.05, min_span=1.0):
    y = np.asarray(y).squeeze()
    y = y[np.isfinite(y)]

    if y.size == 0:
        lo, hi = 0.0, 1.0
    else:
        lo = float(np.min(y))
        hi = float(np.max(y))
        if np.isclose(lo, hi):
            lo -= min_span / 2
            hi += min_span / 2
        else:
            span = hi - lo
            lo -= pad_frac * span
            hi += pad_frac * span

    if bottom is not None:
        lo = max(lo, bottom)
    if top is not None:
        hi = min(hi, top)

    if hi <= lo:
        hi = lo + min_span

    return lo, hi


def _setup_room_pred_fig(
    timestamps: np.ndarray,
    ambient_temps: np.ndarray,
    solar_radiation: np.ndarray,
    n_rooms: int,
    date_fmt: mdates.DateFormatter,
) -> tuple[plt.Figure, dict]:
    n_rows = n_rooms + 1
    height_ratios = [0.8] + [1.15] * n_rooms

    fig = plt.figure(
        figsize=(16, 1.2 + 1.7 * n_rows),
        constrained_layout=True,
    )
    gs = fig.add_gridspec(
        n_rows,
        2,
        height_ratios=height_ratios,
        width_ratios=[1.0, 1.0],
    )

    fig.get_layout_engine().set(
        hspace=0.02,
        wspace=0.05,
        h_pad=0.02,
        w_pad=0.02,
    )

    axes: dict = {}

    ax_amb = fig.add_subplot(gs[0, 0])
    amb = np.asarray(ambient_temps).squeeze()
    ax_amb.plot(timestamps, amb, color="tab:brown", linewidth=1.4)
    ax_amb.set_ylabel("Ambient (°C)", color="tab:brown")
    ax_amb.tick_params(axis="y", labelcolor="tab:brown", labelsize=9)
    ax_amb.set_title("Ambient Temperature", fontsize=11)
    ax_amb.grid(True, alpha=0.25)
    ax_amb.xaxis.set_major_formatter(date_fmt)
    plt.setp(ax_amb.get_xticklabels(), visible=False)
    axes["ambient"] = ax_amb

    ax_sol = fig.add_subplot(gs[0, 1], sharex=ax_amb)
    sol = np.asarray(solar_radiation).squeeze()
    ax_sol.fill_between(timestamps, sol, step="post", color="tab:orange", alpha=0.22)
    ax_sol.step(timestamps, sol, where="post", color="tab:orange", linewidth=1.4)
    ax_sol.set_ylabel("Solar (W/m²)", color="tab:orange")
    ax_sol.tick_params(axis="y", labelcolor="tab:orange", labelsize=9)
    ax_sol.set_title("Solar Radiation", fontsize=11)
    ax_sol.grid(True, alpha=0.25)
    ax_sol.xaxis.set_major_formatter(date_fmt)
    plt.setp(ax_sol.get_xticklabels(), visible=False)
    axes["solar"] = ax_sol

    axes["rooms"] = []

    temp_ref_ax = None
    heat_ref_ax = None

    for i in range(n_rooms):
        row = i + 1

        ax_t = fig.add_subplot(
            gs[row, 0],
            sharex=ax_amb,
            sharey=temp_ref_ax,
        )
        ax_t.set_ylabel(f"Room {i + 1} (°C)")
        ax_t.tick_params(axis="y", labelsize=9)
        ax_t.grid(True, alpha=0.25)
        ax_t.xaxis.set_major_formatter(date_fmt)

        ax_u = fig.add_subplot(
            gs[row, 1],
            sharex=ax_amb,
            sharey=heat_ref_ax,
        )
        ax_u.set_ylabel(f"Heat {i + 1} (W)", color="tab:red")
        ax_u.tick_params(axis="y", labelcolor="tab:red", labelsize=9)
        ax_u.grid(True, alpha=0.25)
        ax_u.xaxis.set_major_formatter(date_fmt)

        if temp_ref_ax is None:
            temp_ref_ax = ax_t
        if heat_ref_ax is None:
            heat_ref_ax = ax_u

        if i < n_rooms - 1:
            plt.setp(ax_t.get_xticklabels(), visible=False)
            plt.setp(ax_u.get_xticklabels(), visible=False)
        # else:
        #     ax_t.set_xlabel("Time")
        #     ax_u.set_xlabel("Time")

        axes["rooms"].append((ax_t, ax_u))

    axes["temp_ref"] = temp_ref_ax
    axes["heat_ref"] = heat_ref_ax
    return fig, axes


def _plot_room_predictions(
    axes: dict,
    timestamps: np.ndarray,
    preds: np.ndarray,
    targets: np.ndarray,
    heat_inputs: np.ndarray,
    hidden_states: np.ndarray,
) -> None:
    n_rooms = targets.shape[0]

    temp_series = [np.asarray(targets), np.asarray(preds)]
    # if hidden_states.size > 0:
    #     temp_series.append(np.asarray(hidden_states[:n_rooms]))

    temp_all = np.concatenate(
        [arr[np.isfinite(arr)] for arr in temp_series if arr.size > 0]
    )
    heat_all = np.asarray(heat_inputs)
    heat_all = heat_all[np.isfinite(heat_all)]

    temp_lo, temp_hi = _safe_step_ylim(temp_all, pad_frac=0.08, min_span=1.0)
    heat_lo, heat_hi = _safe_step_ylim(
        heat_all, bottom=0.0, pad_frac=0.06, min_span=50.0
    )

    axes["temp_ref"].set_ylim(temp_lo, temp_hi)
    axes["heat_ref"].set_ylim(heat_lo, heat_hi)

    tick_lo = np.floor(temp_lo)
    tick_hi = np.ceil(temp_hi)
    if tick_hi - tick_lo <= 12:
        axes["temp_ref"].set_yticks(np.arange(tick_lo, tick_hi + 1, 1.0))

    for i in range(n_rooms):
        ax_t, ax_u = axes["rooms"][i]

        targ = np.asarray(targets[i]).squeeze()
        pred = np.asarray(preds[i]).squeeze()
        heat = np.asarray(heat_inputs[i]).squeeze()

        ax_t.step(
            timestamps,
            targ,
            where="post",
            color="tab:orange",
            linewidth=1.5,
            label="Target" if i == 0 else None,
        )
        ax_t.step(
            timestamps,
            pred,
            where="post",
            color="tab:blue",
            linewidth=1.5,
            linestyle="--",
            label="Prediction" if i == 0 else None,
        )

        # if hidden_states.size > 0 and i < hidden_states.shape[0]:
        #     hid = np.asarray(hidden_states[i]).squeeze()
        #     ax_t.step(
        #         timestamps,
        #         hid,
        #         where="post",
        #         color="tab:green",
        #         linewidth=1.0,
        #         linestyle=":",
        #         alpha=0.7,
        #         label="Hidden state" if i == 0 else None,
        #     )

        if i == 0:
            ax_t.legend(
                loc="upper right",
                framealpha=0.95,
                edgecolor="black",
                fontsize="small",
            )

        ax_u.fill_between(
            timestamps,
            heat,
            step="post",
            color="tab:red",
            alpha=0.22,
        )
        ax_u.step(
            timestamps,
            heat,
            where="post",
            color="tab:red",
            linewidth=1.4,
        )


def _plot_all_rooms_preds_targets_and_ambient(
    data: dict[str, np.ndarray],
    scale_back: bool = True,
    datamodule=None,
) -> plt.Figure:
    timestamps = data["timestamps"]
    preds = np.asarray(data["preds"])
    targets = np.asarray(data["target_temps"])
    ambient_temps = np.asarray(data["ambient_temps"])
    heat_inputs = np.asarray(data["heat_inputs"])
    hidden_states = np.asarray(data["hidden_states"])
    solar_radiation = np.asarray(data["solar_radiation"])

    if scale_back:
        assert datamodule is not None, "Datamodule must be provided for scaling back."

        zone_scaler = datamodule.zone_temp_scaler
        amb_scaler = datamodule.ambient_temp_scaler
        heat_scaler = datamodule.heat_input_scaler
        solar_scaler = datamodule.solar_radiation_scaler

        assert amb_scaler == zone_scaler

        def _inv(arr, scaler):
            arr = np.asarray(arr)
            s = arr.shape
            return scaler.inverse_transform(arr.reshape(-1, 1)).reshape(s)

        preds = _inv(preds, zone_scaler)
        targets = _inv(targets, zone_scaler)
        ambient_temps = _inv(ambient_temps, amb_scaler)
        heat_inputs = _inv(heat_inputs, heat_scaler)
        solar_radiation = _inv(solar_radiation, solar_scaler)
        if hidden_states.size > 0:
            hidden_states = _inv(hidden_states, zone_scaler)

    n_rooms, n_timesteps = targets.shape
    date_fmt = mdates.DateFormatter("%b %d, %H:%M")

    fig, axes = _setup_room_pred_fig(
        timestamps=timestamps,
        ambient_temps=ambient_temps,
        solar_radiation=solar_radiation,
        n_rooms=n_rooms,
        date_fmt=date_fmt,
    )

    _plot_room_predictions(
        axes=axes,
        timestamps=timestamps,
        preds=preds,
        targets=targets,
        heat_inputs=heat_inputs,
        hidden_states=hidden_states,
    )

    duration = (timestamps[-1] - timestamps[0]) / np.timedelta64(1, "h")
    n_hidden = hidden_states.shape[0] if hidden_states.ndim > 0 else 0

    fig.suptitle(
        f"Room Temperature Predictions — {n_timesteps - 1} steps ({duration:.2f} h)",
        fontsize=13,
        # y=1.01,
    )
    fig.align_ylabels()
    fig.autofmt_xdate(rotation=30, ha="right")

    return fig
    # plt.show()


def plot_rooms_data_file(path: Path, datamodule=None) -> None:
    # if path is None:
    #     path = conf.PREDS_DIR / "test_results.npz"
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    # Load data from the npz file
    else:
        data = np.load(path)

    _plot_all_rooms_preds_targets_and_ambient(data, datamodule=datamodule)


def plot_predictions(data, datamodule=None) -> plt.Figure:
    return _plot_all_rooms_preds_targets_and_ambient(data, datamodule=datamodule)


def plot_rooms_data_from_file(data: dict[str, np.ndarray]) -> None:
    assert isinstance(data, dict), "Data should be a dictionary."
    assert all(
        key in data
        for key in ["timestamps", "preds", "targets", "ambient_temps", "heat_inputs"]
    ), (
        "Data dictionary must contain 'timestamps', 'preds', 'targets', 'ambient_temps', and 'heat_inputs'."
    )
    _plot_all_rooms_preds_targets_and_ambient(data)


def to_numpy(tensor: torch.Tensor) -> np.ndarray:
    """
    Converts a PyTorch tensor to a NumPy array.
    Moves the tensor to CPU if it's on a GPU device before conversion [5].
    """
    return tensor.cpu().detach().numpy()


def plot_dataloader(
    dataloader, start: int = 0, horizon: int | None = None, n_rooms: int = 5
) -> None:
    """
    Processes data from a DataLoader and returns it as a dictionary of NumPy arrays.
    """
    assert dataloader.batch_size == 1, (
        "Dataloader must have a batch size of 1 for this function."
    )
    assert start >= 0, "Start index must be non-negative."

    total_len = len(dataloader)
    if horizon is None:
        horizon = total_len - start
    if horizon <= 0:
        raise ValueError("Horizon must be a positive integer.")
    assert total_len - start >= horizon, (
        "The dataloader does not have enough data for the requested horizon."
    )

    # get to start index
    dataiter = iter(dataloader)
    for _ in range(start):
        next(dataiter)

    results = []
    for _ in range(horizon):
        output = {}
        batch = next(dataiter)

        heat_input = (
            batch["thermal_zone"].x[:, -1].view(batch_size, n_rooms, -1).squeeze(-1)
        )  # Last column is heat input, reshape to [B, Z, L-1] and squeeze to [B, Z]
        ambient_temp = batch["environment"].x.view(batch_size, -1)

        target = batch["thermal_zone"].y.view(batch_size, n_rooms, -1).squeeze(-1)

        output["target"] = target
        output["ambient_temp"] = ambient_temp
        output["heat_input"] = heat_input
        output["timestamp"] = batch.timestamp[0]

        results.append(output)

    # Transpose results
    results_dict = {
        key: [res[key] for res in results]
        for key in ["target", "ambient_temp", "heat_input", "timestamp"]
    }

    def format_to_numpy(input):
        return torch.cat(input, dim=0).detach().squeeze().cpu().numpy()

    timestamps = np.array(results_dict["timestamp"]).flatten()
    targets = format_to_numpy(results_dict["target"])
    ambient_temps = format_to_numpy(results_dict["ambient_temp"])
    heat_inputs = format_to_numpy(results_dict["heat_input"])

    data_np = {
        "timestamps": timestamps,
        "targets": targets,
        "ambient_temps": ambient_temps,
        "heat_inputs": heat_inputs,
    }

    _plot_all_rooms_targets_and_ambient(data_np)


if __name__ == "__main__":
    from data_processing.lit_data_modules.RC_5_room_RC_lit_data_module import (
        Rc5RoomHeteroLitDataModule,
    )

    batch_size = 1
    num_workers = 0
    dataset_size = None
    window_size = 6 * 24 * 1  # at 6 samples per hour

    datamodule = Rc5RoomHeteroLitDataModule(
        batch_size=batch_size,
        num_workers=num_workers,
        size=dataset_size,
        window_size=window_size,
    )
    datamodule.setup(stage="test")
    test_loader = datamodule.test_dataloader()
    plot_dataloader(test_loader, start=0, horizon=100, n_rooms=5)
