# CONFIG FILE
# Most of these constants are now handled by Hydra and .yaml files.

import os
from pathlib import Path
from typing import ClassVar

import pandas as pd
import torch

from .utils.paths import paths


class Levels:
    experiment: ClassVar[str] = "experiment_id"
    datetime: ClassVar[str] = "datetime"


SELECTED_MPC_RESULT = "noise_stds[0, 0]_lamda100_Tmargin1.0_h96_sw0.1579_d4b30a49"


CHOSEN_MODEL = (
    Path(paths.log_dir)
    / "vastai/soft_stable_different_noise_levels_1/multiruns/2026-01-13_10-48-22/datamodule.csv_file=five_room_1_year_Ts_0.25_hysteresis-random_Tmargin_1_real.csv_datamodule.noise_stds=[0_0]_experiment=15_minutes_real_hysteresis_random_discrete_soft_stable_observer_solar_1tomany_model.lambda_reg_eigvals=1"
)

# DATALOADER
DATASET_SIZE = None  # None means use the full dataset
NUM_WORKERS = 12  # 12

# ODE SOLVER CONFIG
SOLVER_RTOL = 1e-4  # Relative tolerance for the solver
SOLVER_ATOL = 1e-6  # Absolute tolerance for the solver

# GENERAL MODEL
GRU_HIDDEN_LAYERS = 1
# GRU_HIDDEN_DIM = 64
WINDOW_HOURS = 24 * 3
HORIZON_HOURS = 24
MAX_HORIZON_HOURS = 24


## LINEAR SS NEURAL ODE
ROOM_HIDDEN_STATES_DIM = 15
A_MATRIX_INIT_SCALE = 0.01
B_MATRIX_INIT_SCALE = 0.01
# B_MATRIX_INIT_SCALE = (
#     -4.6
# )  # approx log(0.01) to initialize B matrix with small positive values after softplus

## PORT-HAMILTONIAN MODEL
# HAMILTONIAN_NET_HIDDEN_LAYER_SIZES = [64, 64]
HAMILTONIAN_NET_HIDDEN_LAYER_SIZES = [16, 16]
L2_R_LAMBDA = 0  # 1e-4
L1_G_LAMBDA = 0  # 1e-5
L1_J_LAMBDA = 0  # 1e-5

# TRAINER
ACCELERATOR = "gpu" if torch.cuda.is_available() else "cpu"
GRADIENT_CLIP_VAL = 0.01
SKIP_DATA_ROWS = 0  # currently taken care of in the .csv files from matlab themselves
BATCH_SIZE = 256 * 6
# SKIP_DATA_ROWS = 7000
# BATCH_SIZE = 256
LEARNING_RATE = 2e-4
MIN_LR = 1e-6
WEIGHT_DECAY = 5e-5
MAX_EPOCHS = 2000
ENABLE_CHECKPOINTING = True
SAVE_TOP_K_MODELS = 3
# TRAINER_LOG_EVERY_N_STEP = 50
CHECK_VAL_EVERY_N_EPOCH = 5
HORIZON_SCHEDULER_PATIENCE = 2
HORIZON_SCHEDULER_MIN_DELTA = 0.001

# LR SCHEDULER
# LR_SCHEDULER_THRESHOLD = 2e-4  ## Well working without curriculum training
LR_SCHEDULER_THRESHOLD = 1e-6  # low value to "deactivate" the scheduler
LR_SCHEDULER_FREQUENCY = 5
assert LR_SCHEDULER_FREQUENCY >= CHECK_VAL_EVERY_N_EPOCH, (
    "LR_SCHEDULER_FREQUENCY must be greater than or equal to CHECK_VAL_EVERY_N_EPOCH"
)
# LR_SCHEDULER_PATIENCE = 2  ## Well working without curriculum training
LR_SCHEDULER_PATIENCE = 20
LR_SCHEDULER_FACTOR = 0.5

# EARLY STOPPING
EARLY_STOPPING_PATIENCE = (
    2
    * HORIZON_SCHEDULER_PATIENCE
    * CHECK_VAL_EVERY_N_EPOCH  # early stopping patience needs to be longer than the horizon scheduler patience
)  # number trainer check_val_every_n_epoch epochs without improvement
assert EARLY_STOPPING_PATIENCE % CHECK_VAL_EVERY_N_EPOCH == 0
assert EARLY_STOPPING_PATIENCE > HORIZON_SCHEDULER_PATIENCE, (
    "Early Stopping Patience needs to be longer than the Horizon Scheduler Patience"
)
# Minimum change in the monitored quantity to qualify as an improvement
EARLY_STOPPING_MIN_DELTA = 1e-6

###################################################################################################
# DIRECTORIES
###################################################################################################

try:
    # This works when running as a .py script
    project_root = Path(__file__).resolve().parent.parent
except NameError:
    # This works in interactive sessions (like Jupyter or IPython)
    # It assumes you started the session from the project root.
    project_root = Path(os.getcwd())
PROJECT_ROOT = project_root

# Test paths
TEST_DIR = PROJECT_ROOT / "tests"
FIXTURE_DIR = TEST_DIR / "fixtures"
TEST_DATA_DIR = TEST_DIR / "data"

# Path to the data directory
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
INTERIM_DATA_DIR = DATA_DIR / "interim"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
SCALERS_DIR = DATA_DIR / "scalers"

# Path to the reports directory
REPORTS_DIR = PROJECT_ROOT / "reports"
PLOTS_DIR = REPORTS_DIR / "figures"

# Path to the models directory
MODELS_DIR = PROJECT_ROOT / "src" / "models"
MODEL_CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
PROFILER_LOGS_DIR = MODELS_DIR / "profiler_logs"

# Path to the logs directory
LOGS_DIR = PROJECT_ROOT / "logs"
PREDS_DIR = LOGS_DIR / "predictions"

VIZ_DIR = PROJECT_ROOT / "src" / "analysis"

# Wandb parameters
# WANDB_CACHE_DIR = os.getenv("WANDB_CACHE_DIR")
# WANDB_DIR = os.getenv("WANDB_DIR")

FIVE_ROOM_BRCM_SIMULATION_RESULTS_CSV = (
    DATA_DIR
    / "five_room_horizon_RC_hetero_pyg_inmemory_dataset/raw"
    / "five_room_building_simulation_results.csv"
)

## BRCM BUILDING PARAMETERS
ROOM_AREAS = [84, 84, 84, 132, 36]
###################################################################################################
# OLD Paramaters
###################################################################################################

GRADIENT_CLIP = 1e2
EPOCH_LEARNING_RATE = 0.005

# GAT model parameters
GAT_HEADS = 8
GAT_DROPOUT_PROB = 0.6

# GNN Model parameters
IN_CHANNELS = 14
OUT_CHANNELS = 1
NODE_EMBEDDING_HIDDEN_DIM = 32  # 32 used in paper
NODE_EMBEDDING_DIM = 32  # 32 used in paper
DROPOUT_PROB = 0.3
N_TEMPERATURE_MEASUREMENT_LAGS = 6  # 1 hour (10 minutes intervals)
N_TIME_FEATURES = 6  # cos and sine of 3 different frequencies

###################################################################################################
# Conversion factors
###################################################################################################

J_to_kWh = 1 / 3600000
area = 4982.22  # m2
kBtu_to_kWh = 0.293071
ft2_to_m2 = 0.092903
kBtu_per_ft2_to_kWh_per_m2 = kBtu_to_kWh / ft2_to_m2
Cp = 1005  # J/kg.K

###################################################################################################
# ALPHA BUILDING
###################################################################################################

# SSO profile to use for AWS CLI
AWS_PROFILE = "dev"
# Location of AlphaBuilding Synthetic dataset on S3 bucket
S3_HDF5_FILEPATH = "s3://oedi-data-lake/building_synthetic_dataset/A_Synthetic_Building_Operation_Dataset.h5"
# Alpha Building Synthetic dataset parameters used for validation of the inputs to the RunInfo class
HDF5_FILEPATH = "data/raw/A_Synthetic_Building_Operation_Dataset.h5"
AVAILABLE_CLIMATES = ["1A", "3C", "5A"]
AVAILABLE_RUNS = [1, 2, 3, 4, 5]
AVAILABLE_EFFICIENCIES = ["Standard", "Low", "High"]

# Dateset parameters
DATERANGE = pd.date_range("2006-01-01", "2007-01-01", freq="10min")[:-1]
CLIMATE = "1A"
EFFICIENCY = "Standard"  #'Standard', 'Low', 'High'
RUN = 1
DATA_KEY = "ZonePeopleOccupantCount"
YEAR = "2002"

SITE_VARIABLES = [
    "SiteOutdoorAirDrybulbTemperature",
    "SiteHorizontalInfraredRadiationRateperArea",
]

ZONE_VARIABLES = [
    "ZoneThermostatHeatingSetpointTemperature",
    "ZoneThermostatCoolingSetpointTemperature",
    "ZoneAirTerminalVAVDamperPosition",
    "ZonePeopleOccupantCount",
    "ZoneElectricEquipmentElectricPower",
    "ZoneLightsElectricPower",
    "ZoneMeanAirTemperature",  # this is the target variable
]

BUILDING_VARIABLES = ["SystemNodeTemperature", "SystemNodeMassFlowRate"]

INSIDE_VARIABLES = ZONE_VARIABLES + BUILDING_VARIABLES
VARIABLES = SITE_VARIABLES + ZONE_VARIABLES + BUILDING_VARIABLES

ENERGY_PRICE_SCHEDULE = [
    (0, 0.22),
    (1, 0.21),
    (2, 0.20),
    (3, 0.20),
    (4, 0.21),
    (5, 0.23),
    (6, 0.30),
    (7, 0.38),
    (8, 0.42),
    (9, 0.40),
    (10, 0.36),
    (11, 0.34),
    (12, 0.32),
    (13, 0.31),
    (14, 0.32),
    (15, 0.35),
    (16, 0.40),
    (17, 0.50),
    (18, 0.54),
    (19, 0.48),
    (20, 0.42),
    (21, 0.36),
    (22, 0.30),
    (23, 0.26),
    (24, 0.24),  # Closing point
]

BRCM_MAT_FILE = Path(paths.data_dir) / "building_plant_data.mat"
