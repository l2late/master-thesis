import os
from pathlib import Path

import pandas as pd
import wandb

from alphabuilding.analysis.evaluation import evaluate_model_predictions
from alphabuilding.utils.paths import paths

# %%

ENTITY = os.environ["WANDB_ENTITY"]
PROJECT = os.environ["WANDB_PROJECT"]
PROJECT_PATH = f"{ENTITY}/{PROJECT}"

group_key = "experiment_name"  # None
metric_key = "val/rmse_celsius"  # None


def resolve_artifact(run_id: str, artifact_type: str = "model") -> wandb.Artifact:
    api = wandb.Api()
    run = api.run(f"{PROJECT_PATH}/{run_id}")
    # Get all logged artifacts, filter to models
    model_artifacts = [a for a in run.logged_artifacts() if a.type == artifact_type]

    # Sort by creation time; last one is the latest version
    model_artifacts.sort(key=lambda a: a.created_at)
    latest_model = model_artifacts[-1]

    print(latest_model.name, latest_model.version, latest_model.aliases)
    return latest_model


def download_artifact(artifact: wandb.Artifact) -> Path:
    """Download only if not already cached locally."""
    local_path = Path(paths.artifact_dir) / artifact.name / artifact.version
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


def process_group(df):
    best_run_id = df.loc[df["val/rmse_celsius"].idxmin(), "run_id"]

    api = wandb.Api()
    best_run = api.run(f"{best_run_id}")

    model_artifact = resolve_artifact(best_run_id, artifact_type="model")
    config_artifact = resolve_artifact(best_run_id, artifact_type="config")

    model_artifact_path = download_artifact(model_artifact)
    model_ckpts = list(model_artifact_path.glob("*.ckpt"))
    assert len(model_ckpts) == 1, (
        f"Expected exactly one .ckpt file in the artifact, found {len(model_ckpts)}"
    )
    model_ckpt_path = model_ckpts[0]

    config_artifact_path = download_artifact(config_artifact)
    config_files = list(config_artifact_path.glob("config.yaml"))
    assert len(config_files) == 1, (
        f"Expected exactly one .yaml file in the artifact, found {len(config_files)}"
    )
    config_path = config_files[0]

    evaluate_model_predictions(model_ckpt_path, config_path)


# %%

# Load existing data if available
df_all = pd.read_parquet(os.path.join(paths.output_dir, "wandb_runs_data.parquet"))

GROUP_COLS = [
    "topology",
    "lambda_eigenvals_stability_penalty",
    "noise_stds",
]

for (topology, lambda_, noise_std), df in df_all.groupby(GROUP_COLS):
    print(
        f"\nProcessing topology={topology}, lambda={lambda_}, noise_std={noise_std}..."
    )
    process_group(df)
