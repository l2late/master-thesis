import ast
import os
from collections import defaultdict
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import wandb
from plotly.subplots import make_subplots

from alphabuilding.utils.paths import paths

# ---------------------------
# Configuration
# ---------------------------
ENTITY = os.environ["WANDB_ENTITY"]
PROJECT = os.environ["WANDB_PROJECT"]

group_key = "experiment_name"  # None
metric_key = "val/rmse_celsius"  # None

# %%

project_path = f"{ENTITY}/{PROJECT}"
run_filters = {
    "state": "finished",
    "summary_metrics.epoch": {"$eq": 499},
    "config.model.topology": {
        "$in": ["FULLY_CONNECTED_ONE_TO_ONE", "PHYSICAL_ONE_TO_ONE"]
    },
}
# %%

# api = wandb.Api()
# all_runs = api.runs(
#     project_path,
#     filters=run_filters,
#     lazy=False,
#     per_page=200,
# )

# %%
#
#
# def get_groups(runs) -> list[str]:
#     return sorted({run.group for run in all_runs if run.group is not None})
#
#
# groups = get_groups(all_runs)
#
# print("Discovered groups:", groups)
#
# # For each group, find the run with the best (lowest) final RMSE and collect its information.
#
#
# def get_best_run_for_group(
#     group_name: str, metric_key: str
# ) -> wandb.apis.public.runs.Run | None:
#     print(f"Querying best run for group={g!r}")
#     filters = run_filters | {
#         "group": group_name,
#     }
#     runs = api.runs(
#         f"{ENTITY}/{PROJECT}",
#         filters=filters,
#         order=f"+summary_metrics.{metric_key}",
#     )
#
#     if len(runs) == 0:
#         print(f"  No runs found for group {g!r}, skipping.")
#         return None
#
#     best_run = runs[0]
#     return best_run
#
#
# def get_best_runs_per_group():
#     best_rows = []
#
#     for g in groups:
#         best_run = get_best_run_for_group(g, metric_key)
#         if best_run is None:
#             continue
#
#         rmse = best_run.summary.get(metric_key)
#         if rmse is None:
#             print(f"  Best run {best_run.id} has no {metric_key}, skipping.")
#             continue
#
#         best_rows.append(
#             {
#                 group_key: g,
#                 metric_key: rmse,
#                 "run_id": best_run.id,
#                 "run_name": best_run.name,
#                 "run_path": "/".join(best_run.path),
#                 "run_url": best_run.url,
#             }
#         )
#
#     df_best = pd.DataFrame(best_rows)
#     return df_best
#
#
# df_best = get_best_runs_per_group()
#
# print("\nBest run per group:")
# print(df_best)
# df_best.to_parquet(paths.output_dir / "wandb_best_runs_per_group.parquet")
#
#
# %%


def get_all_runs_data(all_runs: wandb.apis.public.runs.Runs) -> pd.DataFrame:
    data = []
    for ii, run in enumerate(all_runs):
        print(f"Processing run {ii + 1}/{len(all_runs)}: Run ID {run.id}")
        assert metric_key in run.summary, (
            f"Run {run.id} is missing the summary metric '{metric_key}'"
        )
        group_name = run.group
        final_rmse = run.summary.get(metric_key)

        # Filter out runs that might have crashed before logging or are missing the config
        if final_rmse is not None:
            data.append(
                {
                    group_key: group_name,
                    metric_key: final_rmse,
                    "run_id": run.id,
                    "run_name": run.name,
                    "run_path": "/".join(run.path),
                    "run_url": run.url,
                    "epochs": run.summary["epoch"],  # stored as int like 499
                    "topology": run.config["model"][
                        "topology"
                    ],  # stored as string like "FULLY_CONNECTED_ONE_TO_ONE"
                    "noise_stds": run.config[
                        "noise_stds"
                    ],  # stored as string like "[0.0, 0.0]"
                    "lambda_eigenvals_stability_penalty": run.config["model"][
                        "lambda_eigenvals_stability_penalty"
                    ],  # stored as int like 0 or 1
                    "seed": run.config["seed"],  # stored as int like 1000, 1001, etc.
                }
            )

    df = pd.DataFrame(data)

    return df


# wandb_runs_df = get_all_runs_data(all_runs)

# wandb_runs_df.to_parquet(Path(paths.output_dir) / "wandb_runs_data.parquet")

# %%


df = pd.read_parquet(
    Path(paths.output_dir) / "wandb_runs_data.parquet"
)  # Load existing data if available

# %%

epochs_filter = 499

df_filtered = df[df["epochs"] == epochs_filter].copy()
df_filtered = df_filtered[df_filtered["seed"].isin(range(1000, 1050))].copy()

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

# for ax, (noise_label, df_sub) in zip(axes, df_plot.groupby("Noise", sort=False)):
#     ax.set_title(noise_label, y=1.02)
#     sns.boxplot(
#         data=df_sub,
#         x="Topology",
#         y=metric_key,
#         hue="Lambda Penalty",
#         hue_order=lam_order,
#         order=topos_order,
#         palette=[colors[l] for l in lam_order],
#         width=0.6,
#         linewidth=1.0,
#         fliersize=1.5,
#         ax=ax,
#     )
#
#     ax.set_title(noise_label)
#     ax.set_xlabel("")
#     ax.set_ylabel("RMSE" if ax is axes[0] else "")
#     ax.grid(axis="y", linestyle="--", alpha=0.4)
#     ax.legend_.remove()
#
# # Create a single legend outside the last axis
# handles, labels = axes[-1].get_legend_handles_labels()
# fig.legend(
#     handles,
#     labels,
#     title="$\\lambda$ instability penalty coefficient",
#     loc="upper center",
#     bbox_to_anchor=(0.5, 1.0),
#     ncol=2,
#     frameon=False,
# )
# # Global x-label
# fig.supxlabel("RMSE (°C) after 500 epochs, n=50 per experiment", y=0.02, fontsize=10)
# fig.tight_layout(rect=[0, 0, 1, 0.85])  # reserve top 7% for legend
# fig.subplots_adjust(bottom=0.18, wspace=0.15)
#
# # Save high-res for publication
# # fig.savefig("boxplot_topology_lambda_noise.png", bbox_inches="tight")
# box_plot_save_path = Path(paths.report_results_dir)
# fig.savefig(
#     box_plot_save_path / "boxplot_topology_lambda_noise.pdf", bbox_inches="tight"
# )
# plt.show()
# # %%
