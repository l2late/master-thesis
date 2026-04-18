from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import seaborn as sns
from tbparse import SummaryReader

from analysis.midterm_plot_configs import PlotConfig, plot_configs

# Set publication-quality defaults
sns.set_style("whitegrid")
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.figsize": (5, 2.5),
        "figure.dpi": 300,
        "lines.linewidth": 1.5,
        "lines.markersize": 4,
        "axes.linewidth": 0.8,
        "grid.alpha": 0.8,
        "grid.linewidth": 0.8,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def exponential_moving_average(values, alpha):
    """Apply EMA smoothing."""
    smoothed = np.zeros_like(values, dtype=float)
    smoothed[0] = values[0]
    for i in range(1, len(values)):
        smoothed[i] = alpha * values[i] + (1 - alpha) * smoothed[i - 1]
    return smoothed


def plot_training_curves(config: PlotConfig, save_dir: str | None = None):
    fig, ax = plt.subplots()

    colors = sns.color_palette("husl", len(config.log_dirs))

    for log_dir, label, color in zip(config.log_dirs, config.labels, colors):
        reader = SummaryReader(str(log_dir))
        df = reader.scalars

        assert config.metric in df["tag"].values, (
            f"Metric '{config.metric}' not found in log at {log_dir}"
        )
        # Filter metric
        data = df[df["tag"] == config.metric].sort_values("step")
        assert not data.empty, (
            f"No data found for metric '{config.metric}' in {log_dir}"
        )

        if config.skip_steps > 0:
            data = data[data["step"] >= config.skip_steps]
        steps = data["step"].values
        values = data["value"].values

        print(f"Loaded {len(values)} points for '{label}' from {log_dir}")
        # Apply smoothing if requested
        if config.smoothing > 0:
            values = exponential_moving_average(values, config.smoothing)

        ax.plot(steps, values, label=label, color=color, linewidth=1, alpha=0.9)

    if config.use_log_scale:
        ax.set_yscale("log")
        ymin, ymax = ax.get_ylim()
        ax.set_ylim(bottom=min(0.1, ymin), top=ymax)
        ax.yaxis.set_major_locator(
            mticker.LogLocator(base=10.0, subs=(1.0,), numticks=20)
        )

        # 2. Use LogFormatter with minor_thresholds to force labeling of all ticks
        #    This is necessary when using custom LogLocator settings
        ax.yaxis.set_major_formatter(
            mticker.LogFormatterSciNotation(
                base=10.0, labelOnlyBase=False, minor_thresholds=(np.inf, np.inf)
            )
        )
        # Then apply the FuncFormatter to convert scientific notation to plain format
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f"{x:g}"))

    else:
        # Linear scale: simply turn off scientific notation
        formatter = mticker.ScalarFormatter()
        formatter.set_scientific(False)
        formatter.set_useOffset(False)
        ax.yaxis.set_major_formatter(formatter)
        ymin, ymax = ax.get_ylim()
        ax.set_ylim(bottom=min(0, ymin), top=ymax)

    # Formatting
    ax.set_xlabel("Training Step", fontweight="normal")
    ax.set_ylabel(config.ylabel or config.metric.replace("_", " ").title())

    if config.title:
        ax.set_title(config.title, pad=10)

    ax.xaxis.set_major_locator(mticker.MultipleLocator(5000))

    # Place legend to the right of the plot
    ax.legend(
        frameon=True,
        fancybox=False,
        edgecolor="black",
        framealpha=0.95,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
    )

    # Make grid more visible and ensure it is drawn
    ax.grid(True, which="major", linestyle="--", alpha=0.7)

    plt.tight_layout()

    if config.save_filename:
        save_path = Path(config.save_filename).with_suffix(f".{config.save_format}")

        if save_dir:
            save_path = Path(save_dir) / save_path

        fig.savefig(
            save_path,
            format=config.save_format,
            dpi=300,
            bbox_inches="tight",
            facecolor="white" if config.save_format == "png" else None,
        )
        print(f"Saved plot to {save_path}")

    return fig, ax


if __name__ == "__main__":
    from alphabuilding.utils.paths import paths

    plt.close("all")

    figures = []
    for i, config in enumerate(plot_configs):
        print(
            f"Generating plot {i + 1}/{len(plot_configs)}: {config.title or config.metric}"
        )
        fig, ax = plot_training_curves(config, save_dir=paths.root_dir / "figures")
        figures.append((fig, ax))

    plt.show()
    print("All plots generated.")
