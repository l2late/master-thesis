import os
from datetime import datetime
from pathlib import Path

import optuna
from joblib import Parallel, delayed

from alphabuilding.control.sweep_mpc_simulations import (
    # find_experiment_dirs_with_checkpoints,
    optimize_optuna_study_worker,
)
from alphabuilding.control.types import SimulationConfig
from alphabuilding.utils.paths import paths


def run_optuna_sweep(model_path: Path):
    """Run multiple MPC experiments with different settings in parallel"""

    n_total_trials = 5000
    # n_models = 1  # For testing, we take only 2 models. Remove this for full sweep.

    controller_timestep_minutes = 15
    controller_timestep_seconds = controller_timestep_minutes * 60
    plant_timestep_seconds = 30  # can be chosen arbitrarily since the plant simulator uses the continuous-time dynamics and just simulates forward in time. We choose 30s to have a nice integer ratio with the controller timestep, which simplifies the logic for when the controller should step.
    controller_to_plant_step_ratio = int(
        controller_timestep_seconds // plant_timestep_seconds
    )

    mpc_eval_days = 7
    mpc_eval_steps = mpc_eval_days * 24 * 4 * controller_to_plant_step_ratio

    warmup_days = 14
    warmup_steps = warmup_days * 24 * 4 * controller_to_plant_step_ratio

    simulation_config = SimulationConfig(
        warmup_steps=warmup_steps, eval_steps=mpc_eval_steps
    )

    root_output_dir = paths.output_dir / "mpc_hopt"
    root_output_dir.mkdir(parents=True, exist_ok=True)
    assert root_output_dir.exists()

    # Create a unique output directory for this sweep using a timestamp
    output_dir_name_format = "%Y%m%d-%H%M%S"
    sweep_output_dir = root_output_dir / datetime.now().strftime(output_dir_name_format)
    sweep_output_dir.mkdir(parents=True, exist_ok=False)

    # MPC Experiments
    # models_root = paths.log_dir / "vastai" / "soft_stable_different_noise_levels_1"
    # experiment_paths = find_experiment_dirs_with_checkpoints(models_root)
    # model_checkpoints = experiment_paths[:n_models]

    print("Starting Optuna MPC hyperparameter optimization...")

    #  determine the number of parallel jobs to run based on available CPU cores, leaving 2 cores free to avoid overloading the system.
    free_cpus_to_leave = 2
    if os.cpu_count() is not None:
        n_jobs = os.cpu_count() - free_cpus_to_leave
    else:
        n_jobs = 1

    # Calculate how many trials each joblib process should execute
    trials_per_worker = [n_total_trials // n_jobs] * n_jobs
    for i in range(n_total_trials % n_jobs):
        trials_per_worker[i] += 1

    # We tune hyperparameters for each model checkpoint
    # for checkpoint in model_checkpoints:
    # TODO: fix indirection to model checkpoint for testing
    checkpoint = model_path
    print(f"\\n--- Tuning model: {checkpoint.name} ---")

    # use Gaussian Process (Highly recommended for expensive physics simulations)
    n_startup_trials = 200  # 3 * (5 + 5)  # 3 times the number of hyperparameters

    sampler = optuna.samplers.TPESampler(
        n_startup_trials=n_startup_trials,
        multivariate=True,  # Enable multivariate TPE to capture interactions between hyperparameters, which is important for MPC tuning.
    )

    optuna_db_name = "optuna_mpc_tuning.db"
    optuna_db_path = root_output_dir / optuna_db_name
    optuna_sqlite_db = f"sqlite:///{optuna_db_path}"
    # study_name = f"mpc_tuning_{checkpoint.name}"
    # study_name = "mpc_tuning_with_augmented_observer_single_weights_no_margin"
    study_name = "mpc_tuning_matlab_ssopt"

    # Create the study to hold the optimization results. We set load_if_exists=True to allow multiple processes to share the same study and aggregate results in the same database.
    # Each worker process will then load this study, execute its assigned trial, and save results back to the same database, allowing us to aggregate results across all parallel executions seamlessly.
    _ = optuna.create_study(
        study_name=study_name,
        sampler=sampler,
        storage=optuna_sqlite_db,
        directions=["minimize", "minimize"],  # multi-objective optimization
        load_if_exists=True,
    )

    print(f"Parallelizing {n_total_trials} trials across {n_jobs} cores...")

    # Utilize Joblib to sidestep the GIL and execute chunks of the study isolatedly
    Parallel(n_jobs=n_jobs, verbose=10)(
        delayed(optimize_optuna_study_worker)(
            study_name=study_name,
            storage=optuna_sqlite_db,
            n_trials=n_worker_trials,
            model_checkpoint=checkpoint,
            simulation_config=simulation_config,
            output_dir=sweep_output_dir,
        )
        for n_worker_trials in trials_per_worker
        if n_worker_trials > 0
    )

    print("\\nOptuna optimization completed. Best hyperparameters found:")


if __name__ == "__main__":
    model_path = paths.log_dir / "train/runs/2026-03-24_17-37-19"

    run_optuna_sweep(model_path)
