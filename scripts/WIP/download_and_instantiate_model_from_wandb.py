import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import wandb

from alphabuilding.analysis.evaluation import evaluate_model_predictions
from alphabuilding.infrastructure.wandb.utils import (
    WandBPath,
    download_artifact,
)
from alphabuilding.utils.paths import paths

# %%

run_path = WandBPath(
    entity=os.environ["WANDB_ENTITY"],
    project=os.environ["WANDB_PROJECT"],
)

group_key = "experiment_name"  # None
metric_key = "val/rmse_celsius"  # None

# %%

# Load existing data if available
df_all = pd.read_parquet(Path(paths.output_dir) / "wandb_runs_data.parquet")

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
