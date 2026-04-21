import hashlib
import json
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any

import control as ct
import lightning as L
import numpy as np
import pandas as pd
import torch
from hydra.utils import instantiate
from omegaconf import OmegaConf
from pandera.typing import DataFrame as paDataFrame
from tqdm import tqdm

from alphabuilding import constants as global_config
from alphabuilding.control.brcm_building import (
    test_disturbances,
)
from alphabuilding.control.types import MpcConfig, SimulationPhase, TimedStateSpace
from alphabuilding.domain.df_schemas import ControllerInput
from alphabuilding.infrastructure.lightning.datamodules.brcm_datamodule import (
    BRCMTrajectoryLitDataModule,
)
from alphabuilding.utils.chooser import choose_run_dir
from alphabuilding.utils.instantiation import init_module_trained_from_cfg
from alphabuilding.utils.paths import paths
from alphabuilding.utils.state_space import (
    discretize_system,
)

torch.set_grad_enabled(False)

ROOM_AREAS = global_config.ROOM_AREAS

u_cols = [f"u{i + 1}" for i in range(5)]
y_cols = [f"y{i + 1}" for i in range(5)]


def add_comfort_bounds_for_simulation(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Generates Tmin and Tmax sequences for the MPC horizon based on time of day."""

    assert df.index.is_monotonic_increasing, (
        "DataFrame index must be sorted in ascending order."
    )

    set_diff = set(df.index.diff()[1:])  # Exclude first NaT value
    len_set_diff = len(set_diff)
    assert len_set_diff == 1, (
        f"DataFrame index must have a uniform frequency. Got: {len_set_diff} different intervals."
    )

    df["Tmin"] = 16.0
    df["Tmax"] = 25.0

    # Select "Day" times and update them
    # inclusive="both" means [start, end] -> 07:00 and 18:00 included
    day_mask = df.between_time("07:00", "18:00", inclusive="both").index

    df.loc[day_mask, "Tmin"] = 20.0
    df.loc[day_mask, "Tmax"] = 24.0

    return df


def get_controller_input_df(
    brcm_mat_file: Path, datamodule: L.LightningDataModule
) -> paDataFrame[ControllerInput]:
    disturbances_df = test_disturbances(brcm_mat_file, datamodule)
    controller_input_df = add_comfort_bounds_for_simulation(disturbances_df)
    controller_input_df = ControllerInput.validate(controller_input_df)
    return controller_input_df


def load_learned_lti_ss(
    path: Path | None = None,
    auto_select_last: bool = True,
) -> tuple[TimedStateSpace, BRCMTrajectoryLitDataModule, np.ndarray, Any]:
    """Loads learned LTI state-space model and datamodule from trained model.
    Args:
        path: Optional path to the directory containing the checkpoints and Hydra config. If None, prompts user to select.
    """
    # TODO: refactor this monster. Does way too much.
    # List what reponsabilities it currently has and decompose into smaller functions.
    if path is not None and auto_select_last:
        raise ValueError("Cannot specify both 'path' and 'auto_select_last=True'.")

    if path is None:
        logs_root = paths.log_dir
        dir_path = choose_run_dir(logs_root, auto_select_last=auto_select_last)
    else:
        dir_path = path

    checkpoint = dir_path / "checkpoints" / "last.ckpt"
    config_path = dir_path / ".hydra" / "config.yaml"

    cfg = OmegaConf.load(config_path)
    cfg.paths = paths
    # cfg.datamodule.

    # if "workspace" in cfg.datamodule.csv_file:
    #     parts = cfg.datamodule.csv_file.split("/")[-3:]
    #     local_path = paths.data_dir.joinpath(*parts)
    #     cfg.datamodule.csv_file = str(local_path)

    cfg.datamodule.device = "cpu"
    datamodule: BRCMTrajectoryLitDataModule = instantiate(cfg.datamodule)
    # datamodule.setup(stage="fit")
    datamodule.setup()

    module = init_module_trained_from_cfg(cfg, checkpoint)
    module = module.cpu()  # Explicitly move to CPU
    module.eval()  # Set to evaluation mode

    # Get Learned Discrete Filtering Gain K
    # module.observer.gain is shape [Outputs, States] -> Transpose to [States, Outputs] for standard notation
    K_d_torch = module.observer.gain.t().detach()
    K = K_d_torch.T.numpy()  # Shape [States, Outputs]

    # Get Continuous LTI Matrices
    # TODO: place this logic in a common utility function. maybe in the lightning module itself?
    dyn = module.dynamics
    A_c = dyn.A_matrix.detach().cpu().numpy()
    B_c = dyn.B_matrix.detach().cpu().numpy()

    # 3. Discretize EVERYTHING together (System + Observer)
    # Replicating logic from discrete_observer_ode.py -> forward_observer_discrete
    dt_hours = 0.25

    C = module.C.detach()  # Shape [Outputs, States]
    C_np = C.cpu().numpy()

    A_d, B_d = discretize_system(A_c, B_c, C_np, dt_hours=dt_hours)

    n_control_inputs = 5
    n_disturbances = B_d.shape[1] - n_control_inputs

    inputs = [f"u{i + 1}" for i in range(n_control_inputs)]
    disturbances = [f"d{i + 1}" for i in range(n_disturbances)]
    input_labels = inputs + disturbances
    output_labels = [f"y{i + 1}" for i in range(C_np.shape[0])]

    sys = ct.ss(A_d, B_d, C_np, 0, inputs=input_labels, outputs=output_labels)
    sys = TimedStateSpace(sys, dt_hours, "hours")

    return (sys, datamodule, K, cfg)


def _canonicalize_for_hash(obj: Any) -> str:
    """Return a stable JSON string representation suitable for hashing."""
    if isinstance(obj, (dict, list, tuple, str, int, float, bool)) or obj is None:
        data = obj
    else:
        # For dataclasses or OmegaConf configs etc.
        try:
            data = asdict(obj)
        except TypeError:
            data = OmegaConf.to_container(obj, resolve=True)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _config_hash(*parts: Any, length: int = 8) -> str:
    hasher = hashlib.sha256()
    for p in parts:
        hasher.update(_canonicalize_for_hash(p).encode("utf-8"))
    return hasher.hexdigest()[:length]


def save_mpc_experiment_bundle(
    results_df: pd.DataFrame,
    mpc_config: MpcConfig,
    model_hydra_cfg: Any,
    base_output_dir: Path,
    *,
    allow_multiple_runs_per_config: bool = False,
) -> Path:
    # Build a deterministic hash from both configs
    cfg_hash = _config_hash(
        mpc_config, OmegaConf.to_container(model_hydra_cfg, resolve=False)
    )

    # Optional timestamp if you want multiple runs per config
    if allow_multiple_runs_per_config:
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        dir_name = (
            f"h{mpc_config.horizon}_sw{mpc_config.slack_weight}_{cfg_hash}_{timestamp}"
        )
    else:
        lamda_reg_eigvals = model_hydra_cfg.model.lambda_reg_eigvals
        noise_stds = model_hydra_cfg.datamodule.noise_stds
        match = re.search(
            r"Tmargin_(\d+(?:\.\d+)?)", model_hydra_cfg.datamodule.csv_file
        )
        if match:
            t_margin = float(match.group(1))
        else:
            raise ValueError("Could not find Tmargin in csv_file name.")
        dir_name = f"noise_stds{noise_stds}_lamda{lamda_reg_eigvals}_Tmargin{t_margin}_h{mpc_config.horizon}_sw{mpc_config.slack_weight:.4f}_{cfg_hash}"

    exp_dir = base_output_dir / dir_name
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Save datafram
    results_df.to_parquet(exp_dir / "results.parquet")

    # Save configs
    OmegaConf.save(config=model_hydra_cfg, f=exp_dir / "model_config.yaml")
    conf_dict = OmegaConf.create(asdict(mpc_config))
    OmegaConf.save(config=conf_dict, f=exp_dir / "experiment_config.yaml")

    print(f"Experiment saved to: {exp_dir}")
    return exp_dir


# TODO: this is a dirty minimal duplicate of the MPC experiment function, just to run RBC as a reference.
# Needs refactor to remove duplication.
def save_rbc_experiment(
    results_df: pd.DataFrame,
    base_output_dir: Path,
) -> Path:
    exp_dir = base_output_dir
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Save datafram
    results_df.to_parquet(exp_dir / "results.parquet")

    # Save configs
    print(f"Experiment saved to: {exp_dir}")
    return exp_dir


def _process_single_mpc_simulation_parquet_file(
    *,
    result_file: Path,
    filter_Tmargin: float | None = None,
    filter_lambda_reg: int | None = None,
    filter_simulation_phase: SimulationPhase | None = None,
) -> pd.DataFrame | None:
    """
    Helper function to process a single experiment directory using PyArrow pushdown predicates.
    Returns an enriched DataFrame if filters pass, or None if skipped/failed.
    """
    try:
        exp_dir = result_file.parent

        # 1. Load Configs (CPU bound task)
        exp_conf = OmegaConf.load(exp_dir / "experiment_config.yaml")
        model_conf = OmegaConf.load(exp_dir / "model_config.yaml")

        # 2. Extract Metadata
        match = re.search(r"Tmargin_(\d+(?:\.\d+)?)", model_conf.datamodule.csv_file)
        if not match:
            return None  # Skip malformed filenames
        t_margin = float(match.group(1))
        lambda_reg = model_conf.model.lambda_reg_eigvals

        # 3. Apply Metadata Filters (early exit before any file I/O)
        if filter_Tmargin is not None and t_margin != float(filter_Tmargin):
            return None
        if filter_lambda_reg is not None and lambda_reg != float(filter_lambda_reg):
            return None

        # 4. Build Parquet Pushdown Predicates
        filters = []
        if filter_simulation_phase is not None:
            # Assumes 'simulation_phase' is a column inside results.parquet
            filters.append(("simulation_phase", "==", filter_simulation_phase.value))

        # 5. Load Parquet (I/O + CPU task) with Pushdown Predicates
        df = pd.read_parquet(
            result_file, engine="pyarrow", filters=filters if filters else None
        )

        if df.empty:
            return None

        # Format exactly as the original pipeline
        df.index = df.index.set_names(["datetime"])

        # 6. Enrich DataFrame
        df["horizon"] = exp_conf.horizon
        df["slack_weight"] = exp_conf.slack_weight
        df["R_weight"] = exp_conf.R_weight
        df["experiment_id"] = exp_dir.name
        df["Tamb_std"] = model_conf.datamodule.noise_stds[0]
        df["SolRad_std"] = model_conf.datamodule.noise_stds[1]
        df["lambda_reg_eigvals"] = lambda_reg
        df["Tmargin"] = t_margin

        return df

    except Exception:
        # Optionally log error here
        return None


# TODO:  maybe better to use polars for this entire pipeline, since it has better support for lazy evaluation and parallelism out of the box.
def parallel_load_experiment_bundle(
    *,
    root: Path,
    limit: int | None = None,
    filter_Tmargin: float | None = None,
    filter_lambda_reg: int | None = None,
    filter_simulation_phase: SimulationPhase | None = None,
    max_workers: int | None = None,  # Default uses all cores
) -> pd.DataFrame:
    all_runs = []

    # 1. Quickly gather all file paths (Fast generator)
    # Convert to list so we can distribute work
    files = list(root.rglob("results.parquet"))

    if not files:
        raise ValueError("No 'results.parquet' files found in directory.")

    # 2. Parallel Processing
    # Using 'spawn' or 'fork' depending on OS, ProcessPool handles it.
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                _process_single_mpc_simulation_parquet_file,
                result_file=f,
                filter_Tmargin=filter_Tmargin,
                filter_lambda_reg=filter_lambda_reg,
                filter_simulation_phase=filter_simulation_phase,
            ): f
            for f in files
        }

        # Process results as they finish
        # tqdm adds a progress bar
        pbar = tqdm(
            as_completed(futures),
            total=len(files),
            desc="Loading Experiments",
            unit="exp",
        )

        for future in pbar:
            result = future.result()

            if result is not None:
                all_runs.append(result)

                if limit is not None and len(all_runs) >= limit:
                    pbar.write(f"Limit of {limit} experiments reached. Stopping.")

                    # Cancel remaining tasks to save resources (Python 3.9+)
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    if not all_runs:
        raise ValueError("No experiments matched the filter criteria.")

    # 3. Concatenate and Format (Fastest to do once at the end)
    big_df = pd.concat(all_runs, ignore_index=False)
    big_df = big_df.set_index("experiment_id", append=True)
    big_df = big_df.swaplevel(0, 1).sort_index()

    return big_df
