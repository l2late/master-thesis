"""Pareto-front visualization for multi-objective Optuna studies.

Creates static publication-quality Pareto plots (seaborn / matplotlib)
showing non-dominated trials for one or more studies, each with its own
frontier line and colour.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from optuna.study import StudyDirection
from optuna.trial import FrozenTrial

# ── colour palette ───────────────────────────────────────────────────────────

_HIGHLIGHT_COLOUR = "#e74c3c"  # bold red
_HIGHLIGHT_SIZE = 220
_MPC_COLOUR = "#3498db"    # calm blue
_RBC_COLOUR = "#2ecc71"    # green
_FRONTIER_COLOUR_FALLBACK = "#7f8c8d"
_DOMINANT_SIZE = 80

# Predefined study styles  (label, colour)
MPC_STYLE = ("MPC", _MPC_COLOUR)
RBC_STYLE = ("RBC", _RBC_COLOUR)


@dataclass
class ParetoStudy:
    """One Pareto study to render on the shared plot."""
    db_path: Path
    study_name: str
    label: str
    colour: str


def _is_minimisation(study: optuna.study.Study, obj_idx: int) -> bool:
    """Return True if objective *obj_idx* is minimised."""
    return study.directions[obj_idx] == StudyDirection.MINIMIZE


def _build_dominant_df(study: optuna.study.Study) -> pd.DataFrame:
    """Return DataFrame of non-dominated trials in minimisation space.

    Columns: ``x``, ``y``, ``trial_number``.
    """
    dominant: list[FrozenTrial] = study.best_trials
    rows: list[dict[str, Any]] = []
    for t in dominant:
        rows.append(
            {
                "x": t.values[0],
                "y": t.values[1],
                "trial_number": t.number,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["x", "y", "trial_number"])

    # Flip into minimisation space if needed
    if not _is_minimisation(study, 0):
        df["x"] = -df["x"]
    if not _is_minimisation(study, 1):
        df["y"] = -df["y"]
    return df


# ── public API ────────────────────────────────────────────────────────────────


def plot_pareto_dominant(
    studies: list[ParetoStudy],
    target_names: tuple[str, str] | None = None,
    figsize: tuple[float, float] = (9, 6),
    style_context: str = "whitegrid",
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    highlight: Optional[dict] | list[dict] = None,
) -> Figure:
    """Pareto plot showing non-dominated fronts for one or more studies.

    Parameters
    ----------
    studies :
        List of :class:`ParetoStudy` describing each Optuna study to render.
    target_names :
        Human-readable axis labels ``(xlabel, ylabel)``.
        Defaults to ``("Objective 0", "Objective 1")``.
    figsize :
        Matplotlib figure size in inches.
    style_context :
        Seaborn style context name.
    xlim :
        ``(xmin, xmax)``  —  auto-expanded to include all points if not given.
    ylim :
        ``(ymin, ymax)``  —  auto-expanded to include all points if not given.
    highlight :
        A dict with ``x``, ``y`` and optional ``label`` / ``trial_number`` / ``rank``
        for a single trial to highlight, or a ``list[dict]`` to highlight
        multiple trials.  Each highlighted point gets a red star + annotation.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if not studies:
        raise ValueError("At least one ParetoStudy is required.")

    # ── load all dominant DataFrames ─────────────────────────────────────────
    all_dfs: list[pd.DataFrame] = []
    labels: list[str] = []
    colours: list[str] = []
    for ps in studies:
        assert ps.db_path.exists(), f"DB not found: {ps.db_path}"
        study = optuna.load_study(
            study_name=ps.study_name, storage=f"sqlite:///{ps.db_path}"
        )
        if len(study.directions) != 2:
            raise ValueError(
                f"Study '{ps.study_name}' has {len(study.directions)} objectives "
                "(expected 2)."
            )
        df = _build_dominant_df(study)
        all_dfs.append(df)
        labels.append(ps.label)
        colours.append(ps.colour)

    x_label = target_names[0] if target_names else "Objective 0"
    y_label = target_names[1] if target_names else "Objective 1"

    # ── plot ─────────────────────────────────────────────────────────────────
    with sns.axes_style(style_context):
        fig, ax = plt.subplots(figsize=figsize)

        all_x: list[float] = []
        all_y: list[float] = []

        for df, label, colour in zip(all_dfs, labels, colours):
            if df.empty:
                continue

            all_x.extend(df["x"].tolist())
            all_y.extend(df["y"].tolist())

            # Frontier line  (sorted by x, low → high  →  top-left to bottom-right)
            if len(df) >= 2:
                s = df.sort_values("x").reset_index(drop=True)
                ax.plot(
                    s["x"].values,
                    s["y"].values,
                    color=colour,
                    lw=1.5,
                    ls="-",
                    zorder=1,
                    label=label,
                )

            # Points
            sns.scatterplot(
                data=df,
                x="x",
                y="y",
                ax=ax,
                color=colour,
                s=_DOMINANT_SIZE,
                zorder=2,
                alpha=0.75,
                legend=False,
            )

        # Highlighted trial(s)
        highlights = highlight if isinstance(highlight, list) else [highlight] if highlight else []
        for hl in highlights:
            hx, hy = hl["x"], hl["y"]
            label_parts = []
            if "trial_number" in hl:
                label_parts.append(f"Trial {hl['trial_number']}")
            if "rank" in hl:
                label_parts.append(f"rank #{hl['rank']}")
            elif "label" in hl:
                label_parts.append(hl["label"])
            annotation_text = "\n".join(label_parts) if label_parts else None

            ax.scatter(
                hx, hy,
                color=_HIGHLIGHT_COLOUR,
                s=_HIGHLIGHT_SIZE,
                marker="*",
                zorder=5,
                edgecolor="white",
                lw=1.2,
            )
            if annotation_text:
                direction = hl.get("direction", "right")
                if direction == "left":
                    offset = (-18, -12)
                    ha = "right"
                else:
                    offset = (12, 12)
                    ha = "left"
                ax.annotate(
                    annotation_text,
                    xy=(hx, hy),
                    xytext=offset,
                    textcoords="offset points",
                    fontsize=9,
                    fontweight="bold",
                    color=_HIGHLIGHT_COLOUR,
                    ha=ha,
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
        ax.set_title("Pareto Front", fontsize=13, fontweight="bold", pad=12)

        # ── axis limits ──────────────────────────────────────────────────
        if all_x:
            xmin = xlim[0] if xlim else min(all_x)
            xmax = xlim[1] if xlim else max(all_x)
            ymin = ylim[0] if ylim else min(all_y)
            ymax = ylim[1] if ylim else max(all_y)
        else:
            xmin, xmax = xlim or (0, 1)
            ymin, ymax = ylim or (0, 1)

        xpad = (xmax - xmin) * 0.05 if xmax > xmin else 1
        ypad = (ymax - ymin) * 0.05 if ymax > ymin else 1
        ax.set_xlim(xmin - xpad, xmax + xpad)
        ax.set_ylim(ymin - ypad, ymax + ypad)

        # Legend (only line handles, not the scattered points)
        handles, leg_labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, leg_labels, loc="best", framealpha=0.9, edgecolor="gray")

    fig.tight_layout()
    return fig
