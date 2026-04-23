import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import wandb

import alphabuilding.utils.paths as paths


@dataclass
class WandBPath:
    entity: str
    project: str
    run_id: str | None = None

    @property
    def project_path(self) -> str:
        return f"{self.entity}/{self.project}"

    @property
    def run_path(self) -> str:
        if self.run_id is None:
            raise ValueError("run_id must be provided to construct the run path.")
        return f"{self.entity}/{self.project}/{self.run_id}"


def get_best_run_id_from_wandb(
    wandb_path: WandBPath,
    metric_key: str,
    run_filters: dict[str, Any],
    minimize: bool = True,
    api: wandb.Api | None = None,
) -> str:
    """
    Retrieve the run_id of the best model based on a specified metric.

    Args:
        wandb_path: WandBPath object containing the entity and project.
        metric_key: The metric to evaluate (e.g., 'val/rmse_celsius').
        run_filters: Dictionary of MongoDB-style filters to apply to the runs.
        minimize: If True, the best run has the lowest metric value (ascending order).
                  If False, the best run has the highest metric value (descending order).
        api: Optional wandb.Api instance. If not provided, a new one will be created.

    Returns:
        The run_id (str) of the best performing run.

    Raises:
        ValueError: If no runs match the provided filters.
    """
    if api is None:
        api = wandb.Api()

    # W&B sorting: "+" for ascending (minimize), "-" for descending (maximize)
    order_prefix = "+" if minimize else "-"
    order = f"{order_prefix}summary_metrics.{metric_key}"

    # Query W&B for runs matching the filters, ordered by the metric
    runs = api.runs(
        path=f"{wandb_path.entity}/{wandb_path.project}",
        filters=run_filters,
        order=order,
        per_page=1,  # Optimization: we only need the first run
    )

    # Get the first run from the paginated response
    best_run = next(iter(runs), None)

    if best_run is None:
        raise ValueError(
            f"No runs matched the filters in {wandb_path.entity}/{wandb_path.project}."
        )

    return best_run.id


def resolve_artifact(
    wandb_path: WandBPath, artifact_type: str = "model"
) -> wandb.Artifact:
    api = wandb.Api()
    run = api.run(wandb_path.run_path)
    # Get all logged artifacts, filter to models
    model_artifacts = [a for a in run.logged_artifacts() if a.type == artifact_type]

    # Sort by creation time; last one is the latest version
    model_artifacts.sort(key=lambda a: a.created_at)
    latest_model = model_artifacts[-1]

    print(latest_model.name, latest_model.version, latest_model.aliases)
    return latest_model


def download_artifact(
    artifact: wandb.Artifact, download_dir: Path | None = None
) -> Path:
    """Download only if not already cached locally."""

    if download_dir is None:
        download_dir = Path(paths.artifact_dir)

    local_path = download_dir / artifact.name / artifact.version

    if not local_path.exists():
        print(
            f"Downloading artifact {artifact.name} version {artifact.version} to {local_path}..."
        )
        artifact.download(root=str(local_path))

    else:
        print(
            f"Artifact {artifact.name} version {artifact.version} already exists locally at {local_path}. Skipping download."
        )

    return local_path


def download_model_checkpoint_from_wandb(
    run_path: WandBPath,
    download_dir: Path | None = None,
) -> Path:
    """
    Download the model checkpoint artifact from WandB.

    Args:
        run_path: WandBPath with entity, project, and run_id set.
        download_dir: Optional directory to cache the artifact in.
                      Defaults to `paths.artifact_dir`.

    Returns:
        Path to the downloaded .ckpt file.
    """
    model_artifact = resolve_artifact(run_path, artifact_type="model")

    model_artifact_path = download_artifact(model_artifact, download_dir=download_dir)
    model_ckpts = list(model_artifact_path.glob("*.ckpt"))
    assert len(model_ckpts) == 1, (
        f"Expected exactly one .ckpt file in the artifact, found {len(model_ckpts)}"
    )
    model_ckpt_path = model_ckpts[0]
    return model_ckpt_path


def download_config_artifact_from_wandb(
    run_path: WandBPath,
    download_dir: Path | None = None,
) -> Path:
    """
    Download the config artifact from WandB.

    Args:
        run_path: WandBPath with entity, project, and run_id set.
        download_dir: Optional directory to cache the artifact in.
                      Defaults to `paths.artifact_dir`.

    Returns:
        Path to the downloaded config.yaml file.
    """
    config_artifact = resolve_artifact(run_path, artifact_type="config")
    config_artifact_path = download_artifact(config_artifact, download_dir=download_dir)
    config_files = list(config_artifact_path.glob("config.yaml"))
    assert len(config_files) == 1, (
        f"Expected exactly one .yaml file in the artifact, found {len(config_files)}"
    )
    config_path = config_files[0]
    return config_path


def get_run_metadata_from_wandb(wandb_path: WandBPath) -> dict:
    """
    Fetch all metadata for a WandB run (config, summary, tags, etc.).

    Args:
        wandb_path: WandBPath with entity, project, and run_id set.

    Returns:
        Dict with keys: config, summary, tags, name, url
    """
    api = wandb.Api()
    run = api.run(wandb_path.run_path)
    return {
        "config": dict(run.config),
        "summary": dict(run.summary),
        "tags": run.tags,
        "name": run.name,
        "url": run.url,
    }


# def process_group(df):
#     best_run_id = df.loc[df["val/rmse_celsius"].idxmin(), "run_id"]
#
#     wandb_path = WandBPath(
#         entity=os.environ["WANDB_ENTITY"],
#         project=os.environ["WANDB_PROJECT"],
#         run_id=best_run_id,
#     )
#
#     # api = wandb.Api()
#     # best_run = api.run(f"{best_run_id}")
#     model_ckpt_path = download_model_checkpoint(wandb_path)
#     config_path = download_config_artifact_from_wandb(wandb_path)
#
#     evaluate_model_predictions(model_ckpt_path, config_path)
#
#
# def get_best_run_for_group(
#     wandb_path: WandBPath, group_name: str, metric_key: str, filters: dict | None = None
# ) -> wandb.apis.public.runs.Run | None:
#     api = wandb.Api()
#     print(f"Querying best run for group={g!r}")
#
#     if filters is None:
#         filters = {}
#     filters = filters | {
#         "group": group_name,
#     }
#
#     runs = api.runs(
#         wandb_path.project_path,
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
# def get_best_runs_per_group(
#     groups: list[str], wandb_path: WandBPath, metric_key: str
# ) -> pd.DataFrame:
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


def get_all_runs_data(
    all_runs: wandb.apis.public.runs.Runs, metric_key: str, group_key: str
) -> pd.DataFrame:
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


# def get_wandb_runs_df(
#     run_path: WandBPath, group_key: str, metric_key: str
# ) -> pd.DataFrame:
#     api = wandb.Api()
#     runs = api.runs(run_path.project_path)
#     # Create a DataFrame with run_id, group, and metric
#     data = []
#     for run in runs:
#         run_id = run.id
#         group = run.config.get(group_key, "ungrouped") if group_key else "ungrouped"
#         metric = (
#             run.summary.get(metric_key, float("inf")) if metric_key else float("inf")
#         )
#         data.append({"run_id": run_id, "group": group, "metric": metric})
#     df = pd.DataFrame(data)
#     # Group by the specified key and find the run with the best (lowest) metric in each group
#     best_runs = df.loc[df.groupby("group")["metric"].idxmin()]
#     return best_runs
