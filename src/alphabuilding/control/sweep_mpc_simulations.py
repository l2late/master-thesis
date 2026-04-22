import os
from pathlib import Path

import optuna
from optuna.storages import BaseStorage, RDBStorage

from alphabuilding.application.use_cases.load_n4sid_model import load_matlab_n4sid_model

# CRITICAL: Set these BEFORE importing numpy/torch to prevent CPU oversubscription.
# We want 8 processes, each using 1 core, rather than 8 processes each fighting for 8 cores.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
# Hide all GPUs from PyTorch, we do this all on CPU
os.environ["CUDA_VISIBLE_DEVICES"] = ""


import numpy as np

from alphabuilding import constants as global_config
from alphabuilding.control.brcm_building import (
    BRCMBuildingSimulator,
)
from alphabuilding.control.controllers import (
    EconomicMPCController,
    MPCSolverError,
    RbcController,
)
from alphabuilding.control.model_provision import ModelBundle
from alphabuilding.control.performance_metrics import (
    total_comfort_violation_kelvin_hours,
    total_energy_consumption_watt_hour,
)
from alphabuilding.control.simulation import run_simulation
from alphabuilding.control.state_estimation import (
    AugmentedLuenbergerObserver,
    FilteringLuenbergerObserver,
    build_augmented_system,
    check_detectability_pbh,
    check_observability,
    conditioning_report,
    design_augmented_gain,
)
from alphabuilding.control.storage_strategy import StorageConfig, create_storage
from alphabuilding.control.types import (
    MpcConfig,
    MpcSimulationConfig,
    SimulationConfig,
    SimulationPhase,
)
from alphabuilding.control.utils import (
    get_controller_input_df,
    load_learned_lti_ss,
    save_mpc_experiment_bundle,
    save_rbc_experiment,
)
from alphabuilding.domain.types import Scalers
from alphabuilding.utils.paths import paths

NP_ROOM_AREAS = np.array(global_config.ROOM_AREAS)


def find_experiment_dirs_with_checkpoints(
    root_dir: str | Path, glob_pattern: str = "checkpoints"
) -> list[Path]:
    """
    Recursively finds all directories that contain a 'glob_pattern' subdirectory.
    Args:
        root_dir: The high-level directory to start searching from.
    Returns:
        A sorted list of absolute Path objects to the found directories
        (the parent of the 'glob_pattern' folder).
    """
    root_path = Path(root_dir).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Root directory not found: {root_path}")
    # rglob("checkpoints") finds all folders named 'checkpoints' recursively
    # We take the .parent to get the experiment directory (e.g., .../datamodule.csv_file=...)
    experiment_dirs = [
        ckpt_dir.parent
        for ckpt_dir in root_path.rglob(glob_pattern)
        if ckpt_dir.is_dir()
    ]
    return sorted(experiment_dirs)


class IncrementalPruningCallback:
    def __init__(
        self,
        trial,
        warmup_steps,
        steps_per_day,
        dt_hours,
        n_startup_trials=5,
        prune_after_n_days=2,
    ):
        self._trial = trial
        self._warmup_steps = warmup_steps
        self._steps_per_day = steps_per_day
        self._dt_hours = dt_hours
        self._eval_step = 0
        self._cumulative_kh = 0.0

        self._n_startup_trials = n_startup_trials
        self._prune_after_n_days = prune_after_n_days

        # Cache the threshold so we only query the DB once per trial
        self._cached_median_kh = None

    def __call__(self, step, y, tmin, tmax):
        if step < self._warmup_steps:
            return

        viol = (
            np.maximum(0, tmin - y) + np.maximum(0, y - tmax)
        ).sum() * self._dt_hours
        self._cumulative_kh += viol
        self._eval_step += 1

        if self._eval_step % self._steps_per_day == 0:
            day = self._eval_step // self._steps_per_day
            attr_key = f"step_{day}_kh"
            self._trial.set_user_attr(attr_key, self._cumulative_kh)

            if day < self._prune_after_n_days:
                return

            # If we haven't calculated the median threshold yet for this trial, fetch it
            if self._cached_median_kh is None:
                completed_trials = self._trial.study.get_trials(
                    deepcopy=False, states=[optuna.trial.TrialState.COMPLETE]
                )

                if len(completed_trials) >= self._n_startup_trials:
                    past_values = [
                        t.user_attrs[attr_key]
                        for t in completed_trials
                        if attr_key in t.user_attrs
                    ]
                    if past_values:
                        self._cached_median_kh = np.median(past_values)

            # Prune using the cached median
            if self._cached_median_kh is not None:
                if self._cumulative_kh > self._cached_median_kh:
                    raise optuna.TrialPruned()


def run_single_mpc_experiment(
    *,
    config: MpcSimulationConfig,
    output_dir,
    save_results=False,
    # Pass the Optuna trial for reporting intermediate results, if applicable
    trial: optuna.Trial | None = None,
) -> tuple[float, float]:
    """
    Runs a single MPC simulation for specific parameters.
    This function isolates the logic to be run in a separate process.
    """
    # Load plant inside worker to ensure thread safety and fresh state
    brcm_mat_file = global_config.BRCM_MAT_FILE
    plant = BRCMBuildingSimulator.from_mat_file(brcm_mat_file)

    # Load model with checkpoint

    sys_learned, dm, Kd_learned, hydra_cfg = load_learned_lti_ss(
        path=config.mpc.model_checkpoint, auto_select_last=False
    )

    # FIX: for testing with the N4SID model, we load the model from the MATLAB .mat file instead of the PyTorch checkpoint.
    # we do need the datamodule and hydra_cfg however, so we need to make sure that the matlab
    # model was trained on the same data and with the same scalers as defined in the datamodule.
    # path_to_matlab_data = Path(paths.data_dir) / "matlab" / "optimal_lti_matrices.mat"
    # sys_learned, Kd_learned = load_matlab_n4sid_model(path_to_matlab_data)

    scalers = Scalers(
        temp=dm.zone_temp_scaler,
        amb=dm.ambient_temp_scaler,
        sol=dm.solar_radiation_scaler,
        heat=dm.heat_input_scaler,
    )

    A = sys_learned.system.A
    B = sys_learned.system.B
    C = sys_learned.system.C

    nd = 5  #  input disturbance for rooms
    nx = sys_learned.system.A.shape[0]

    std_x_phys = 0.01
    std_d_phys = 0.05
    std_y_phys = 1e-6

    # Convert standard deviations to physical variances (°C^2)
    qx_phys = std_x_phys**2
    qd_phys = std_d_phys**2
    ry_phys = std_y_phys**2

    # The variance of the scaler
    var_scale_factor = scalers.temp.base_scaler.scale_**2

    # Translate to the "scaled world" for the Riccati solver
    qx = qx_phys / var_scale_factor
    qd = qd_phys / var_scale_factor
    ry = ry_phys / var_scale_factor

    A_aug, B_aug, C_aug = build_augmented_system(A, B, C, nd)

    # conditioning_report(A_aug, C_aug, nd)

    rank, n_aug, is_obs = check_observability(A_aug, C_aug)
    # print(f"Observability rank: {rank} / {n_aug}  →  fully observable: {is_obs}")

    undetectable_modes = check_detectability_pbh(A_aug, C_aug)
    assert not undetectable_modes, (
        f"PBHautus test failed: {len(undetectable_modes)} undetectable modes found. Observer design may not be feasible."
    )

    K_aug, Q_aug, R_y = design_augmented_gain(
        A_aug, C_aug, nx=nx, nd=nd, qx=qx, qd=qd, ry=ry
    )

    # print("K_aug shape:", K_aug.shape)  # expect (nx+nd, ny)
    # print("eig((I - K C) A) (magnitudes):")
    # eig_obs = np.linalg.eigvals((np.eye(nx + nd) - K_aug @ C_aug) @ A_aug)
    # print(np.sort(np.abs(eig_obs))[::-1][:10])

    observer = AugmentedLuenbergerObserver(
        A_aug=A_aug,
        B_aug=B_aug,
        C_aug=C_aug,
        K_aug=K_aug,
        nx=nx,
        nd=nd,
        # x0=np.zeros(nx),  # or plant.x[:nx] if you prefer
        # start with true initial state for faster convergence in this test
        x0=plant.x[:nx],
        scalers=scalers,
    )

    u_min_W_m2 = np.zeros(5)
    u_max_W_m2 = np.ones(5) * 35.0

    # %%
    rbc_controller = RbcController(
        n_actuators=5,
        u_min=u_min_W_m2,
        u_max=u_max_W_m2,
        deadband=np.ones(5) * 0.5,
    )

    empc_controller = EconomicMPCController(
        model=sys_learned,
        horizon=config.mpc.horizon,
        R_weights=config.mpc.R_weights,
        slack_weights=config.mpc.slack_weights,
        lambda_du=config.mpc.lambda_du,
        u_min_physical=u_min_W_m2,
        u_max_physical=u_max_W_m2,
        scalers=scalers,
        margins=config.mpc.margins,
    )

    controller_input_df = get_controller_input_df(brcm_mat_file, dm)

    results_df = run_simulation(
        plant=plant,
        warmup_controller=rbc_controller,
        eval_controller=empc_controller,
        observer=observer,
        df=controller_input_df,
        config=config.simulation,
        # optuna_pruning_callback=daily_pruning_callback,
    )

    # TODO: output result from function. save resuls outside
    if save_results:
        save_mpc_experiment_bundle(
            results_df=results_df,
            mpc_config=config.mpc,
            model_hydra_cfg=hydra_cfg,
            base_output_dir=output_dir,
        )

    results_df = results_df[
        results_df["simulation_phase"] == SimulationPhase.EVALUATION
    ]

    total_energy = total_energy_consumption_watt_hour(results_df)
    total_violation = total_comfort_violation_kelvin_hours(results_df)

    return total_energy, total_violation


def run_single_rbc_experiment(
    *,
    config: MpcSimulationConfig,
    output_dir,
    save_results=False,
    # Optuna trial for pruning callbacks (optional)
    trial: optuna.Trial | None = None,
    # Hyperparameter overrides (used during hopt)
    u_max_override: np.ndarray | None = None,
    deadband_override: np.ndarray | None = None,
):
    """
    Runs a single RBC simulation for specific parameters.

    Args:
        config: Simulation configuration (model checkpoint is used for observer).
        output_dir: Directory for optional result saving.
        save_results: Whether to persist simulation output.
        trial: Optuna trial for intermediate reporting / pruning.
        u_max_override: Override per-actuator max heating power (W/m²).
        deadband_override: Override per-actuator hysteresis band (°C).
    """
    brcm_mat_file = global_config.BRCM_MAT_FILE
    plant = BRCMBuildingSimulator.from_mat_file(brcm_mat_file)

    sys_learned, dm, L_learned, hydra_cfg = load_learned_lti_ss(
        path=config.mpc.model_checkpoint, auto_select_last=False
    )

    scalers = Scalers(
        temp=dm.zone_temp_scaler,
        amb=dm.ambient_temp_scaler,
        sol=dm.solar_radiation_scaler,
        heat=dm.heat_input_scaler,
    )

    observer = FilteringLuenbergerObserver(
        Ad=sys_learned.system.A,
        Bd=sys_learned.system.B,
        C=sys_learned.system.C,
        Kd=L_learned,
        x0=np.zeros(sys_learned.system.A.shape[0]),
        scalers=scalers,
    )

    u_min_W_m2 = np.zeros(5)
    u_max_W_m2 = u_max_override if u_max_override is not None else np.ones(5) * 50.0
    db = deadband_override if deadband_override is not None else np.ones(5) * 0.5

    rbc_controller = RbcController(
        n_actuators=5,
        u_min=u_min_W_m2,
        u_max=u_max_W_m2,
        deadband=db,
    )

    controller_input_df = get_controller_input_df(brcm_mat_file, dm)

    results_df = run_simulation(
        plant=plant,
        warmup_controller=rbc_controller,
        eval_controller=rbc_controller,
        observer=observer,
        df=controller_input_df,
        config=config.simulation,
        optuna_pruning_callback=None,  # can be wired up later if needed
    )

    if save_results:
        save_rbc_experiment(
            results_df=results_df,
            base_output_dir=output_dir,
        )

    results_df = results_df[
        results_df["simulation_phase"] == SimulationPhase.EVALUATION
    ]

    total_energy = total_energy_consumption_watt_hour(results_df)
    total_violation = total_comfort_violation_kelvin_hours(results_df)

    return total_energy, total_violation


def empc_objective(
    trial: optuna.Trial,
    model_bundle: ModelBundle,
    simulation_config: SimulationConfig,
    output_dir: Path,
) -> tuple[float, float]:
    """Optuna (multi) objective function to define the search space and evaluate a trial."""

    n_zones = 5  # Number of temperature states/slack variables
    n_actuators = n_zones  # Number of control inputs

    # 1. Generate lists of floats for Q and R dynamically
    # Optuna will register these as "R_weight_1", "R_weight_2", etc.
    # R_weights = [
    #     trial.suggest_float(f"R_weight_{i + 1}", low=1e-2, high=1e3, log=True)
    #     for i in range(n_actuators)
    # ]
    #
    # slack_weights = [
    #     trial.suggest_float(f"slack_weight_{i + 1}", low=1e-1, high=1e4, log=True)
    #     for i in range(n_zones)
    # ]

    R_weights = np.ones(n_actuators) * trial.suggest_float(
        "R_weight", low=1e-2, high=1e3, log=True
    )

    slack_weights = np.ones(n_zones) * trial.suggest_float(
        "slack_weight", low=1e-1, high=1e4, log=True
    )

    lambda_du = trial.suggest_float(
        "lambda_du", low=1e1, high=1e5, log=True
    )

    # horizon_hours = 4
    # horizon_hours = trial.suggest_categorical(
    #     "horizon_hours", [8]
    # )  # MPC horizons in hours
    horizon_hours = 24
    horizon = horizon_hours * 4

    # Optional, margins for the min and max soft temperature consstraints.
    # Can help reduce on constraint violations when there is too much model mismatch
    # margins = [
    #     trial.suggest_float(f"margin_{i + 1}", low=0.0, high=1.0)
    #     for i in range(n_zones)
    # ]
    margins = np.zeros(n_zones)  # for testing without margins
    # Construct your simulation configuration
    config = MpcSimulationConfig(
        mpc=MpcConfig(
            model_checkpoint=model_bundle.run_dir,
            horizon=horizon,
            slack_weights=np.array(slack_weights),
            R_weights=np.array(R_weights),
            lambda_du=lambda_du,
            margins=np.array(margins),
        ),
        simulation=simulation_config,
    )

    try:
        # Tip: Set save_results=False during wide exploratory tuning to save I/O overhead.
        total_energy, total_violation = run_single_mpc_experiment(
            config=config, output_dir=output_dir, save_results=False, trial=trial
        )
        return total_energy, total_violation
    except MPCSolverError:
        return (
            np.inf,
            np.inf,
        )  # Return a very bad score if the MPC optimization fails, so that Optuna learns to avoid that region of the search space


# --------------------------------------------------------------------------- #
#  RBC Hyperparameter Optimisation                                            #
# --------------------------------------------------------------------------- #


def rbc_objective(
    trial: optuna.Trial,
    model_bundle: ModelBundle,
    simulation_config: SimulationConfig,
    output_dir: Path,
) -> tuple[float, float]:
    """Optuna multi-objective function for RBC hyperparameter tuning.

    Searches over:
      - u_max       : per-actuator maximum heating power (W/m²)
      - deadband    : per-actuator hysteresis deadband (°C)

    Returns (total_energy_wh, total_comfort_violation_Kh).
    """
    n_actuators = 5
    u_max_value = trial.suggest_float("u_max", low=1.0, high=35.0, log=True)
    u_max = np.ones(n_actuators) * u_max_value

    deadband_value = trial.suggest_float("deadband", low=0.1, high=3.0, log=True)
    deadband = np.ones(n_actuators) * deadband_value

    config = MpcSimulationConfig(
        mpc=MpcConfig(
            model_checkpoint=model_bundle.run_dir,
            horizon=0,
            slack_weights=np.zeros(n_actuators),
            R_weights=np.zeros(n_actuators),
            lambda_du=0.0,
        ),
        simulation=simulation_config,
    )

    try:
        total_energy, total_violation = run_single_rbc_experiment(
            config=config,
            output_dir=output_dir,
            save_results=False,
            trial=trial,
            u_max_override=u_max,
            deadband_override=deadband,
        )
        return total_energy, total_violation
    except Exception:
        return (np.inf, np.inf)


def optimize_optuna_study_worker(
    study_name: str,
    storage_config: StorageConfig,
    n_trials: int,
    model_bundle: ModelBundle,
    simulation_config: SimulationConfig,
    output_dir: Path,
):
    """Worker function executed by joblib to run trials sequentially within one process.

    Storage is created inside each worker to ensure clean state and proper
    process isolation.  The StorageConfig is a frozen dataclass and
    serialises cleanly across joblib workers.
    """
    storage = create_storage(storage_config)

    if isinstance(storage, str):
        # SQLite / MySQL URL string — wrap in RDBStorage
        rdb = RDBStorage(
            url=storage,
            engine_kwargs={"connect_args": {"timeout": 60}},
        )
        study: BaseStorage = rdb
    else:
        # JournalStorage instance
        study = storage

    study = optuna.load_study(study_name=study_name, storage=study)
    study.optimize(
        lambda trial: empc_objective(
            trial, model_bundle, simulation_config, output_dir
        ),
        n_trials=n_trials,
    )


def optimize_rbc_optuna_study_worker(
    study_name: str,
    storage_config: StorageConfig,
    n_trials: int,
    model_bundle: ModelBundle,
    simulation_config: SimulationConfig,
    output_dir: Path,
):
    """Worker function for RBC hyperparameter optimisation.

    Identical structure to :func:`optimize_optuna_study_worker` but targets
    the RBC objective function instead of MPC.
    """
    storage = create_storage(storage_config)

    if isinstance(storage, str):
        rdb = RDBStorage(
            url=storage,
            engine_kwargs={"connect_args": {"timeout": 60}},
        )
        study: BaseStorage = rdb
    else:
        study = storage

    study = optuna.load_study(study_name=study_name, storage=study)
    study.optimize(
        lambda trial: rbc_objective(trial, model_bundle, simulation_config, output_dir),
        n_trials=n_trials,
    )
