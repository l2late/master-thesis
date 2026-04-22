"""Pareto-front visualization for multi-objective Optuna studies.

Creates static publication-quality Pareto plots (seaborn / matplotlib)
showing only non-dominated trials, with an optional highlight for a
selected ranked trial (e.g. the output of ``_sorted_best_trial``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from optuna.study import StudyDirection
from optuna.trial import FrozenTrial

from alphabuilding.infrastructure.optuna.study_analysis import (
    RankedTrial,
    _to_minimisation_space,
)

# ── colour palette ───────────────────────────────────────────────────────────

_HIGHLIGHT_COLOUR = "#e74c3c"  # bold red
_DOMINANT_COLOUR = "#3498db"  # calm blue
_FRONTIER_COLOUR = "#7f8c8d"  # muted gray
_HIGHLIGHT_SIZE = 220
_DOMINANT_SIZE = 80


def _is_minimisation(study: optuna.study.Study, obj_idx: int) -> bool:
    """Return True if objective *obj_idx* is minimised."""
    return study.directions[obj_idx] == StudyDirection.MINIMIZE


def _build_pareto_dataframe(
    study: optuna.study.Study,
    highlight_trial: RankedTrial | None = None,
) -> pd.DataFrame:
    """Return a DataFrame of all Pareto-optimal (non-dominated) trials.

    Columns: ``x``, ``y``, ``trial_number``, ``is_best``.
    ``x`` and ``y`` are always in **minimisation space** so the plot
    reads naturally (bottom-left = ideal point).
    """
    dominant: list[FrozenTrial] = study.best_trials
    rows: list[dict[str, Any]] = []

    for t in dominant:
        is_best = (
            highlight_trial is not None and t.number == highlight_trial.trial.number
        )
        rows.append(
            {
                "x": t.values[0],
                "y": t.values[1],
                "trial_number": t.number,
                "is_best": is_best,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        # ensure columns exist even with zero rows
        return pd.DataFrame(columns=["x", "y", "trial_number", "is_best"])

    # Flip axes into minimisation space for display
    if not _is_minimisation(study, 0):
        df["x"] = -df["x"]
    if not _is_minimisation(study, 1):
        df["y"] = -df["y"]

    return df


def _frontier_steps(df: pd.DataFrame) -> pd.DataFrame:
    """Build L-shaped step-line coordinates for the Pareto frontier.

    The input *df* is already in minimisation space (lower is better).
    Sorting by x and walking descending creates the step staircase.
    """
    if len(df) < 2:
        return df[["x", "y"]].copy()

    sorted_df = df.sort_values("x").reset_index(drop=True)
    xs, ys = [], []
    for i, row in sorted_df.iterrows():
        if i == 0:
            xs.append(row["x"])
            ys.append(row["y"])
            continue

        # Horizontal segment from previous point to current x
        xs.append(row["x"])
        ys.append(ys[-1])  # hold y
        # Vertical segment to current y
        xs.append(row["x"])
        ys.append(row["y"])

    return pd.DataFrame({"x": xs, "y": ys})


# ── public API ────────────────────────────────────────────────────────────────


def plot_pareto_dominant(
    db_path: Path,
    study_name: str,
    highlight_trial: RankedTrial | None = None,
    target_names: list[str] | None = None,
    figsize: tuple[float, float] = (9, 6),
    style_context: str = "whitegrid",
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
) -> Figure:
    """Pareto plot showing only non-dominated trials for a 2-objective study.

    Parameters
    ----------
    db_path :
        Path to the SQLite ``*.db`` file.
    study_name :
        Name of the Optuna study inside the database.
    highlight_trial :
        If given, this trial is marked with a star and an annotation showing
        its trial number and rank.  Typically the output of
        ``_sorted_best_trial()``.
    target_names :
        Human-readable axis labels.  Defaults to ``["Objective 0", "Objective 1"]``.
    figsize :
        Matplotlib figure size in inches.
    style_context :
        Seaborn style context name (passed to ``sns.axes_style``).
    xlim :
        Tuple of ``(xmin, xmax)`` to set the X-axis limits.  Useful for
        zooming into a region of interest when objectives span a wide range.
    ylim :
        Tuple of ``(ymin, ymax)`` to set the Y-axis limits.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    ValueError
        If the study does not have exactly 2 objectives.
    """
    assert db_path.exists(), f"Optuna database not found at {db_path}"

    study = optuna.load_study(study_name=study_name, storage=f"sqlite:///{db_path}")
    if len(study.directions) != 2:
        raise ValueError(
            f"Expected a 2-objective study, got {len(study.directions)}. "
            f"Directions: {study.directions}"
        )

    # ── data ─────────────────────────────────────────────────────────────────
    df = _build_pareto_dataframe(study, highlight_trial)
    if df.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(
            0.5,
            0.5,
            "No Pareto-optimal trials found.",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
            color="gray",
        )
        ax.set_xlabel(target_names[0] if target_names else "Objective 0")
        ax.set_ylabel(target_names[1] if target_names else "Objective 1")
        return fig

    dominant_df = df[~df["is_best"]]
    best_df = df[df["is_best"]]
    x_label = target_names[0] if target_names else "Objective 0"
    y_label = target_names[1] if target_names else "Objective 1"

    # ── plot ─────────────────────────────────────────────────────────────────
    with sns.axes_style(style_context):
        fig, ax = plt.subplots(figsize=figsize)

        # Frontier step line
        frontier = _frontier_steps(df)
        if len(frontier) >= 2:
            sns.lineplot(
                data=frontier,
                x="x",
                y="y",
                ax=ax,
                color=_FRONTIER_COLOUR,
                lw=1.5,
                ls="--",
                zorder=1,
                label="Pareto frontier",
            )

        # All dominant trials
        sns.scatterplot(
            data=dominant_df,
            x="x",
            y="y",
            ax=ax,
            color=_DOMINANT_COLOUR,
            s=_DOMINANT_SIZE,
            zorder=2,
            alpha=0.75,
            label="Non-dominated trials",
        )

        # Highlighted trial
        if not best_df.empty:
            sns.scatterplot(
                data=best_df,
                x="x",
                y="y",
                ax=ax,
                color=_HIGHLIGHT_COLOUR,
                s=_HIGHLIGHT_SIZE,
                marker="*",
                zorder=5,
                edgecolor="white",
                lw=1.2,
                label=f"Best trial (#{best_df.iloc[0]['trial_number']})",
            )

            # Annotation
            row = best_df.iloc[0]
            trial_num = int(row["trial_number"])
            rank_text = (
                f"rank #{highlight_trial.rank}" if highlight_trial is not None else ""
            )
            ax.annotate(
                f"Trial {trial_num}\n{rank_text}".strip(),
                xy=(row["x"], row["y"]),
                xytext=(12, 12),
                textcoords="offset points",
                fontsize=9,
                fontweight="bold",
                color=_HIGHLIGHT_COLOUR,
                arrowprops=dict(
                    arrowstyle="->",
                    color=_HIGHLIGHT_COLOUR,
                    lw=1.2,
                    connectionstyle="arc3,rad=0.15",
                ),
                zorder=6,
            )

        ax.set_xlabel(x_label, fontsize=11)
        ax.set_ylabel(y_label, fontsize=11)
        ax.set_title(
            "Pareto Front",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )

        # Axis limits
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)

        # Clean legend
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, labels, loc="best", framealpha=0.9, edgecolor="gray")

    fig.tight_layout()
    return fig
