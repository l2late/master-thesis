import ast
import os
from pathlib import Path

import pandas as pd
import wandb

from alphabuilding.infrastructure.wandb.utils import (
    WandBPath,
    get_all_runs_data,
)
from alphabuilding.utils.paths import paths

# ---------------------------
# Configuration
# ---------------------------
wandb_path = WandBPath(
    entity=os.environ["WANDB_ENTITY"], project=os.environ["WANDB_PROJECT"]
)

group_key = "experiment_name"
metric_key = "val/rmse_celsius"

# %%

epochs = 499
run_filters = {
    "state": "finished",
    "summary_metrics.epoch": {"$eq": epochs},
    "config.model.topology": {
        "$in": ["FULLY_CONNECTED_ONE_TO_ONE", "PHYSICAL_ONE_TO_ONE"]
    },
    "config.seed": {"$in": list(range(1000, 1050))},
}
# %%

api = wandb.Api()

all_runs = api.runs(
    wandb_path.project_path,
    filters=run_filters,
    # lazy=False, # lazy false is faster but can seem very slow
    per_page=20,
)

# groups = sorted({run.group for run in all_runs if run.group is not None})
#
# print("Discovered groups:", groups)

# %%


wandb_runs_df = get_all_runs_data(all_runs, metric_key=metric_key, group_key=group_key)

wandb_runs_df.to_parquet(Path(paths.output_dir) / "wandb_runs_data.parquet")

# %%


df = pd.read_parquet(
    Path(paths.output_dir) / "wandb_runs_data.parquet"
)  # Load existing data if available

# %%

epochs_filter = epochs

df_filtered = df[df["epochs"] == epochs_filter].copy()
# df_filtered = df_filtered[df_filtered["seed"].isin(range(1000, 1050))].copy()

# Parse noise_stds strings like "[0.0, 0.0]" -> (0.0, 0.0)
df_filtered["noise_stds"] = df_filtered["noise_stds"].apply(
    lambda s: tuple(ast.literal_eval(s)) if isinstance(s, str) else tuple(s)
)

topology_names = ["Fully Connected", "Physical"]
# Map topologies and DROP unconstrained
df_filtered["Topology"] = df_filtered["topology"].replace(
    {
        "FULLY_CONNECTED_ONE_TO_ONE": topology_names[0],
        "PHYSICAL_ONE_TO_ONE": topology_names[1],
        # everything else (e.g. UNCONSTRAINED) will be filtered out below
    }
)
df_filtered = df_filtered[df_filtered["Topology"].isin(topology_names)].copy()

df_filtered["Lambda Penalty"] = df_filtered["lambda_eigenvals_stability_penalty"].map(
    {0: "λ = 0", 1: "λ = 1"}
)

noise_levels = sorted(df_filtered["noise_stds"].unique())
# drop the first one (0, 0)
# noise_levels = noise_levels[1:]

lam_order = ["λ = 0", "λ = 1"]
topos_order = topology_names
colors = {"λ = 0": "#EF553B", "λ = 1": "#636EFA"}

import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", font_scale=1)
plt.rcParams.update(
    {
        "figure.dpi": 200,
        "savefig.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 1.0,
    }
)

# Restrict to the noise levels you want (you already skipped the first)
df_plot = df_filtered[df_filtered["noise_stds"].isin(noise_levels)].copy()

# Nice string labels for noise
df_plot["Noise"] = df_plot["noise_stds"].apply(
    lambda t: r"$\sigma_{temp}=" f"{t[0]:.2f}$, " r"$\sigma_{solar}" f"={t[1]:.1f}$"
)

# Sort categorical columns for consistent ordering
df_plot["Topology"] = pd.Categorical(
    df_plot["Topology"], categories=topos_order, ordered=True
)
df_plot["Lambda Penalty"] = pd.Categorical(
    df_plot["Lambda Penalty"], categories=lam_order, ordered=True
)
df_plot["Noise"] = pd.Categorical(
    df_plot["Noise"], categories=sorted(df_plot["Noise"].unique()), ordered=True
)

# One column per noise level
n_noise = len(df_plot["Noise"].unique())

fig, axes = plt.subplots(
    1,
    n_noise,
    figsize=(3 * n_noise, 7),
    sharey=True,
)

if n_noise == 1:
    axes = [axes]

for ax, (noise_label, df_sub) in zip(axes, df_plot.groupby("Noise", sort=False)):
    ax.set_title(noise_label, y=1.02)

    # Replaced sns.boxplot with sns.violinplot
    sns.violinplot(
        data=df_sub,
        x="Topology",
        y=metric_key,
        hue="Lambda Penalty",
        hue_order=lam_order,
        order=topos_order,
        palette=[colors[l] for l in lam_order],
        width=0.8,  # Slightly wider looks better for violins
        linewidth=1.0,
        inner="quartile",  # Shows quartile lines inside the violin
        split=True,  # Splits the violin in half since there are exactly 2 hues
        ax=ax,
    )

    ax.set_title(noise_label)
    ax.set_xlabel("")
    ax.set_ylabel("RMSE" if ax is axes[0] else "")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend_.remove()

# Create a single legend outside the last axis (moved to bottom)
handles, labels = axes[-1].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    title="$\\lambda$ instability penalty coefficient",
    loc="upper center",
    bbox_to_anchor=(0.5, 0.15),  # Anchors the legend at the bottom center
    ncol=2,
    frameon=False,
)

# Global title moved to the top
fig.suptitle("RMSE (°C) after 500 epochs (n=50 per experiment)", y=0.95, fontsize=16)

# Adjust layout to reserve bottom space for the legend and top space for the title
fig.tight_layout(rect=[0, 0.15, 1, 0.95])
fig.subplots_adjust(bottom=0.25, wspace=0.15)

# Save high-res for publication
box_plot_save_path = Path(paths.report_results_dir)
# Updated the filename to reflect the new plot type
fig.savefig(
    box_plot_save_path / "violinplot_topology_lambda_noise.pdf", bbox_inches="tight"
)
plt.show()
print("Done")
