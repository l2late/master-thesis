from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from pandera.typing import DataFrame

from alphabuilding.control.types import SimulationPhase
from alphabuilding.domain.df_schemas import SimulationResult

from ..constants import ROOM_AREAS

NP_ROOM_AREAS = np.array(ROOM_AREAS)

date_fmt = mdates.DateFormatter("%m-%d %H:%M")


def validate_consistency(results: dict[str, Any]):
    """
    Ensures all simulation results share the same environment (Tamb, SolRad)
    and constraints (Tmin, Tmax).
    """
    if not results:
        raise ValueError("No results provided to plot.")

    # Use the first item as the reference
    ref_name = next(iter(results))
    ref_df = results[ref_name]

    # Extract reference arrays for comparison
    ref_tamb = ref_df["Tamb"].to_numpy()
    ref_sol = ref_df["SolRad"].to_numpy()
    ref_bounds = ref_df[["Tmin", "Tmax"]].to_numpy()

    for name, df in results.items():
        if name == ref_name:
            continue

        SimulationResult.validate(df)

        # Check lengths match first
        if len(df) != len(ref_df):
            raise ValueError(
                f"Length mismatch: {name} has {len(df)} steps, {ref_name} has {len(ref_df)}"
            )

        # Check Bounds
        if not np.allclose(df[["Tmin", "Tmax"]].to_numpy(), ref_bounds, atol=1e-5):
            raise ValueError(f"Comfort bounds mismatch in {name} vs {ref_name}")

        # Check Ambient Temp
        if not np.allclose(df["Tamb"].to_numpy(), ref_tamb, atol=1e-1):
            raise ValueError(f"Ambient temperature mismatch in {name} vs {ref_name}")

        # Check Solar Rad
        if not np.allclose(df["SolRad"].to_numpy(), ref_sol, atol=10):
            raise ValueError(f"Solar radiation mismatch in {name} vs {ref_name}")


def setup_simulation_fig(ref_df: SimulationResult, date_fmt):
    """
    Creates the figure layout and plots STATIC data (Disturbances, Bounds).
    Returns the figure and a dictionary of axes.
    """
    total_steps = ref_df.shape[0]
    sim_steps = total_steps - 1
    t_dates = ref_df.index[0 : sim_steps + 1]

    tamb_data = ref_df["Tamb"].to_numpy()
    sol_data = ref_df["SolRad"].to_numpy()
    bounds = ref_df[["Tmin", "Tmax"]].to_numpy().T

    fig = plt.figure(figsize=(19.2, 10.8))
    gs = fig.add_gridspec(6, 2, height_ratios=[1.2, 1, 1, 1, 1, 1])

    axes = {}

    # --- TOP LEFT: Disturbances (Plot ONCE) ---
    ax_dist = fig.add_subplot(gs[0, 0])
    axes["dist"] = ax_dist

    color = "tab:brown"
    ax_dist.set_ylabel("Ambient Temp (°C)", color=color)
    ax_dist.plot(t_dates, tamb_data, color=color, linewidth=1.5, label="Ambient")
    ax_dist.tick_params(axis="y", labelcolor=color)
    ax_dist.set_title("Disturbances: Ambient & Solar")
    ax_dist.grid(True, alpha=0.3)
    ax_dist.xaxis.set_major_formatter(date_fmt)

    # Secondary Axis
    ax_sol = ax_dist.twinx()
    axes["sol"] = ax_sol
    color = "tab:orange"
    ax_sol.set_ylabel("Solar Rad (W/m²)", color=color)
    ax_sol.fill_between(t_dates, sol_data, color=color, alpha=0.3, label="Solar Rad")
    ax_sol.tick_params(axis="y", labelcolor=color)

    # --- TOP RIGHT: Total Power Placeholder ---
    ax_pow = fig.add_subplot(gs[0, 1], sharex=ax_dist)
    axes["total_power"] = ax_pow
    ax_pow.set_ylabel("Total Power (W)")
    ax_pow.set_title("Total Power")
    ax_pow.grid(True, alpha=0.3)
    ax_pow.xaxis.set_major_formatter(date_fmt)

    # --- ROWS 1-5: Zones ---
    axes["zones"] = []
    for i in range(5):
        row_idx = i + 1

        # Temp Axis
        ax_t = fig.add_subplot(gs[row_idx, 0], sharex=ax_dist)

        # Plot Bounds ONCE
        ax_t.fill_between(
            t_dates,
            bounds[0, :],
            bounds[1, :],
            color="gray",
            alpha=0.2,
            label="Comfort Range" if i == 0 else None,
        )

        ax_t.set_ylabel(f"Zone {i + 1} Temp")
        ax_t.grid(True, alpha=0.3)

        # Power Axis
        ax_u = fig.add_subplot(gs[row_idx, 1], sharex=ax_dist)
        ax_u.set_ylabel(f"Zone {i + 1} Power")
        ax_u.grid(True, alpha=0.3)

        # Hide x-labels for inner plots
        if i < 4:
            plt.setp(ax_t.get_xticklabels(), visible=False)
            plt.setp(ax_u.get_xticklabels(), visible=False)

        axes["zones"].append((ax_t, ax_u))

    return fig, axes


def plot_single_result(axes, df, name, color):
    """
    Plots the variable traces (y, u) for ONE controller onto existing axes.
    """
    t_dates = df.index
    y = df[["y1", "y2", "y3", "y4", "y5"]].to_numpy()
    u = df[["u1", "u2", "u3", "u4", "u5"]].to_numpy()

    # 1. Plot Total Power
    total_power = np.sum(u, axis=1)
    ax = axes["total_power"]
    ax.step(t_dates, total_power, where="post", color=color, linewidth=1.5, label=name)
    # For a specific axis 'ax'
    ax.ticklabel_format(useOffset=False, style="plain", axis="y")
    ax.set_ylim([0, NP_ROOM_AREAS.sum() * 50 + 200])  # Start power y-axis at 0

    # 2. Plot Zones
    for i in range(5):
        ax_t, ax_u = axes["zones"][i]

        # Temperature
        ax_t.plot(
            t_dates, y[:, i], color=color, linewidth=1.5, label=name if i == 0 else None
        )

        # Power
        ax_u.step(t_dates, u[:, i], where="post", color=color, alpha=0.8, linewidth=1.5)
        ax_u.set_ylim([0, NP_ROOM_AREAS[i] * 50 + 200])  # Start power y-axis at 0
        # For a specific axis 'ax'
        ax_u.ticklabel_format(useOffset=False, style="plain", axis="y")


def plot_simulation_results_multiple_controllers(
    *,
    results: dict[str, DataFrame[SimulationResult]],
    date_fmt: str = "%Y-%b-%d %H:%M",
) -> plt.Figure:
    mdate_fmt = mdates.DateFormatter(date_fmt)
    validate_consistency(results)

    # Setup Figure using the first result as reference
    ref_name = next(iter(results))
    ref_df = results[ref_name]
    fig, axes = setup_simulation_fig(ref_df, mdate_fmt)

    # 3. Loop and Plot
    # Define a color cycle manually or use a colormap
    colors = ["tab:blue", "tab:red", "tab:purple", "tab:cyan", "tab:green"]

    for i, (name, df) in enumerate(results.items()):
        c = colors[i % len(colors)]
        plot_single_result(axes, df, name, color=c)

    # 4. Final Polish (Legends, Layout)
    # Add legend to Total Power
    axes["total_power"].legend(loc="upper left", framealpha=1.0, edgecolor="black")

    # Add legend to First Zone Temp (includes Comfort Range)
    axes["zones"][0][0].legend(
        loc="upper left", framealpha=1.0, edgecolor="black", fontsize="small"
    )

    fig.autofmt_xdate()
    fig.suptitle(f"Controller Comparison: {', '.join(results.keys())}", fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])

    return fig


def plot_observer_convergence(
    df: DataFrame[SimulationResult],
    n_rooms: int = 5,
) -> plt.Figure:

    e_prior_cols = [f"obs_prior_err{i + 1}" for i in range(n_rooms)]
    e_post_cols = [f"obs_post_err{i + 1}" for i in range(n_rooms)]

    prior_errors = df[e_prior_cols].to_numpy()
    posterior_errors = df[e_post_cols].to_numpy()

    prior_rms = np.sqrt(np.nanmean(prior_errors**2, axis=1))
    posterior_rms = np.sqrt(np.nanmean(posterior_errors**2, axis=1))

    index = pd.to_datetime(df.index)
    eval_mask = df["simulation_phase"] == SimulationPhase.EVALUATION
    t_eval_start = index[eval_mask.to_numpy()][0]

    ROOM_COLORS = plt.cm.tab10.colors[:n_rooms]
    RMS_STYLE = dict(color="black", lw=1.8, ls="--", zorder=5)
    EVAL_STYLE = dict(color="#c0392b", lw=1.2, ls=":", zorder=6)
    ZERO_STYLE = dict(color="gray", lw=0.6, ls="-")

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(14, 12),
        sharex=True,
        gridspec_kw={"height_ratios": [2.5, 1.5, 2.5, 1.5]},
    )
    fig.suptitle(
        "Observer Diagnostic: Prior vs. Posterior Output Error",
        fontsize=13,
        fontweight="bold",
        y=1.01,
    )

    # ── Row 1: Prior per-room ──────────────────────────────────────────────────
    ax = axes[0]
    for i in range(n_rooms):
        ax.plot(
            index,
            prior_errors[:, i],
            lw=0.9,
            alpha=0.75,
            color=ROOM_COLORS[i],
            label=f"Room {i + 1}",
        )
    ax.plot(index, prior_rms, label="RMS", **RMS_STYLE)
    ax.axvline(t_eval_start, **EVAL_STYLE, label="Eval start")
    ax.axhline(0, **ZERO_STYLE)
    ax.set_ylabel("Error (°C)")
    ax.set_title(
        r"Prior output error  $\;e_{\mathrm{prior}}(k) = y(k) - C\,\hat{x}(k|k{-}1)$",
        fontsize=10,
        loc="left",
    )
    ax.legend(ncol=4, fontsize=8, framealpha=0.85)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ── Row 2: Prior RMS, log scale ────────────────────────────────────────────
    ax = axes[1]
    ax.plot(index, np.abs(prior_rms), color="black", lw=1.4)
    ax.axvline(t_eval_start, **EVAL_STYLE)
    ax.set_yscale("log")
    ax.set_ylabel("|RMS| (°C)")
    ax.set_title("Prior |RMS|  (log scale)", fontsize=10, loc="left")
    ax.yaxis.set_minor_locator(ticker.LogLocator(subs="all"))

    # ── Row 3: Posterior per-room ──────────────────────────────────────────────
    ax = axes[2]
    for i in range(n_rooms):
        ax.plot(
            index,
            posterior_errors[:, i],
            lw=0.9,
            alpha=0.75,
            color=ROOM_COLORS[i],
            label=f"Room {i + 1}",
        )
    ax.plot(index, posterior_rms, label="RMS", **RMS_STYLE)
    ax.axvline(t_eval_start, **EVAL_STYLE, label="Eval start")
    ax.axhline(0, **ZERO_STYLE)
    ax.set_ylabel("Error (°C)")
    ax.set_title(
        r"Posterior output error  $\;e_{\mathrm{post}}(k) = y(k) - C\,\hat{x}(k|k)$",
        fontsize=10,
        loc="left",
    )
    ax.legend(ncol=4, fontsize=8, framealpha=0.85)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ── Row 4: Posterior RMS, log scale ───────────────────────────────────────
    ax = axes[3]
    ax.plot(index, np.abs(posterior_rms), color="steelblue", lw=1.4)
    ax.axvline(t_eval_start, **EVAL_STYLE)
    ax.set_yscale("log")
    ax.set_ylabel("|RMS| (°C)")
    ax.set_title("Posterior |RMS|  (log scale)", fontsize=10, loc="left")
    ax.set_xlabel("Datetime")
    ax.yaxis.set_minor_locator(ticker.LogLocator(subs="all"))
    return fig
