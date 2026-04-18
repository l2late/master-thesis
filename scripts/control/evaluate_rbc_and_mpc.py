import logging
import time

import numpy as np
import pandas as pd
import torch

from alphabuilding import constants as global_config
from alphabuilding.control.brcm_building import (
    BRCMBuildingSimulator,
    validation_disturbances,
)
from alphabuilding.control.controllers import EconomicMPCController, RbcController
from alphabuilding.control.performance_metrics import hvac_control_performance_metrics
from alphabuilding.control.simulation import run_simulation
from alphabuilding.control.state_estimation import (
    AugmentedLuenbergerObserver,
    build_augmented_system,
    check_detectability_pbh,
    check_observability,
    conditioning_report,
    design_augmented_gain,
)
from alphabuilding.control.types import SimulationConfig, SimulationPhase
from alphabuilding.control.utils import (
    get_controller_input_df,
    load_learned_lti_ss,
)
from alphabuilding.control.visualization import (
    plot_observer_convergence,
    plot_simulation_results_multiple_controllers,
)
from alphabuilding.domain.types import Scalers
from alphabuilding.infrastructure.optuna.study_analysis import (
    controller_params_from_trial,
    get_sorted_best_trials,
    list_study_names,
)
from alphabuilding.utils.logging_config import setup_logging
from alphabuilding.utils.paths import paths

NP_ROOM_AREAS = np.array(global_config.ROOM_AREAS)

torch.set_grad_enabled(False)


setup_logging(level=logging.INFO)
logging.getLogger("alphabuilding.control").setLevel(logging.INFO)

# %%

# ------------------------------------------------------------------------------------------------
## MPC Settings
mpc_horizon_hours = 16
max_rad_power_W_m2 = 35.0  # Watts/m2 : make sure this is the same value as that used for the MPC hyperparameter optimization in `bayesian_optimization_mpc_weights.py`, since we will be comparing the MPC results to the RBC results with the same power limits, and we want to make sure the comparison is fair and that the expected RBC results we are comparing to were generated with the same power limits.
u_min_W_m2 = np.zeros(5)
u_min_W = NP_ROOM_AREAS * u_min_W_m2
u_max_W_m2 = np.ones(5) * max_rad_power_W_m2
u_max_W = NP_ROOM_AREAS * u_max_W_m2

# ------------------------------------------------------------------------------------------------
plant_step_length_seconds = 30
# Controller model is discretized at 15 minute intervals, so we need to run the plant for 15 minutes between each controller step
controller_step_length_seconds = 15 * 60
controller_steps_per_hour = int(3600 // controller_step_length_seconds)
assert controller_steps_per_hour == 4
controller_steps_per_plant_step = (
    controller_step_length_seconds / plant_step_length_seconds
)

## -----------------------------------------------------------------------------------------------
## WARMUP AND SIMULATION SETTINGS
warm_up_days = 14
warmup_steps = int(
    warm_up_days * 24 * controller_steps_per_hour * controller_steps_per_plant_step
)  # warmup for the simulation for 15 days using only the RBC to allow building and the observer to converge before we start recording results for performance evaluation

eval_days = 7
eval_hours = eval_days * 24
eval_steps = int(
    eval_hours * controller_steps_per_hour * controller_steps_per_plant_step
)

# ------------------------------------------------------------------------------------------------
sys_learned, dm, Kd_learned, cfg = load_learned_lti_ss(auto_select_last=False)

scalers = Scalers(
    temp=dm.zone_temp_scaler,
    amb=dm.ambient_temp_scaler,
    sol=dm.solar_radiation_scaler,
    heat=dm.heat_input_scaler,
)

df = validation_disturbances(global_config.BRCM_MAT_FILE, dm)
controller_input_df = get_controller_input_df(global_config.BRCM_MAT_FILE, dm)

EXPECTED_RBC_TEST_DATA = paths.test_data_dir / "expected_rbc_simulation_results.parquet"

expected_rbc_results_df = pd.read_parquet(EXPECTED_RBC_TEST_DATA)
# Infer frequency because parquet files don't preserve it, and it's needed for the assertion to work correctly
expected_rbc_results_df.index.freq = pd.infer_freq(expected_rbc_results_df.index)
expected_rbc_results_df = expected_rbc_results_df[: eval_steps + 1]

plant = BRCMBuildingSimulator.from_mat_file(global_config.BRCM_MAT_FILE)

A = sys_learned.system.A
B = sys_learned.system.B
C = sys_learned.system.C

nd = 5  #  input disturbance for rooms
nx = sys_learned.system.A.shape[0]

# If the state estimates overshoot the actual measurements during fast transients: The model is too stiff. Increase std_x_phys to allow the states to adapt faster.
std_x_phys = 0.05  # State process noise: how much the RC model drifts per step (this might be higher given how the model is identified)
# If MPC has a steady-state error (e.g., room is always 0.5°C too cold): The disturbance isn't integrating fast enough. Increase std_d_phys.
std_d_phys = 0.01  # Disturbance drift: how fast the unmeasured disturbance changes (very slow for this case as it should model slow ambient disturbances such as ground temperature, solar rad or ambient temp)
# if MPC control actions are extremely jittery: The observer is reacting to sensor noise. Increase std_y_phys or decrease std_d_phys.
std_y_phys = 0.0  # Measurement noise: None in this simulation

# Convert standard deviations to physical variances (°C^2)
qx_phys = std_x_phys**2
qd_phys = std_d_phys**2
ry_phys = std_y_phys**2

# The scaler's standard deviation (how many °C equals "1.0" in the scaled world)
# If scalers.temp was fitted on multiple columns, you can take the mean()
sigma_temp = np.mean(scalers.temp.base_scaler.scale_)
# The variance of the scaler
var_scale_factor = sigma_temp**2

# Translate to the "scaled world" for the Riccati solver
qx = qx_phys / var_scale_factor
qd = qd_phys / var_scale_factor
ry = ry_phys / var_scale_factor

A_aug, B_aug, C_aug = build_augmented_system(A, B, C, nd)

## Sanity Checks
conditioning_report(A_aug, C_aug, nd)
rank, n_aug, is_obs = check_observability(A_aug, C_aug)
print(f"Observability rank: {rank} / {n_aug}  →  fully observable: {is_obs}")
modes = check_detectability_pbh(A_aug, C_aug)
if not modes:
    print("DETECTABLE ✓ — augmented observer design is feasible")
else:
    print(f"WARNING: {len(modes)} undetectable mode(s): {modes}")


K_aug, Q_aug, R_y = design_augmented_gain(
    A_aug, C_aug, nx=nx, nd=nd, qx=qx, qd=qd, ry=ry
)

print("K_aug shape:", K_aug.shape)  # expect (nx+nd, ny)
print("eig((I - K C) A) (magnitudes):")
eig_obs = np.linalg.eigvals((np.eye(nx + nd) - K_aug @ C_aug) @ A_aug)
print(np.sort(np.abs(eig_obs))[::-1][:10])

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

# %%

rbc_controller = RbcController(
    n_actuators=5,
    u_min=u_min_W_m2,
    u_max=u_max_W_m2,
    deadband=np.ones(5) * 0.5,
)
simulation_config = SimulationConfig(
    warmup_steps=warmup_steps,
    eval_steps=eval_steps,
)

# %%
#
rbc_results_df = run_simulation(
    plant=plant,
    warmup_controller=rbc_controller,
    eval_controller=rbc_controller,
    observer=observer,
    config=simulation_config,
    df=controller_input_df,
)
# # testing_rbc_results_df = rbc_results_df[: len(expected_rbc_results_df)][
# #     expected_rbc_results_df.columns
# # ]
# # pd.testing.assert_frame_equal(
# #     testing_rbc_results_df[: len(expected_rbc_results_df)], expected_rbc_results_df
# # )  # for u_max = 50Watts

# %%

optuna_db_path = paths.log_dir / "mpc_hopt" / "offset-free" / "optuna_studies.db"
assert optuna_db_path.exists(), f"Optuna database not found at {optuna_db_path}"

# Discover available study names
list_of_study_names = list_study_names(optuna_db_path)
print(list_of_study_names)

study_name = "mpc_tuning_with_augmented_observer_single_weights_no_margins"
assert study_name in list_of_study_names, (
    f"Study name '{study_name}' not found in database. Available studies: {list_of_study_names}"
)


# %%

# Unbiased: closest to the ideal point
ranked = get_sorted_best_trials(
    study_name=study_name,
    db_path=optuna_db_path,
    strategy="weighted_sum",
    # strategy="utopia",
    weights=[4, 5],  # [Comfort, Energy]
)

R_weights, slack_penalty_weights, margins = controller_params_from_trial(ranked[0])
# R_weights = np.ones(5) * 132
# slack_penalty_weights = np.ones(5) * 68
margins = np.zeros(5)


mpc_controller = EconomicMPCController(
    model=sys_learned,
    horizon=mpc_horizon_hours * controller_steps_per_hour,
    R_weights=R_weights,
    slack_weights=slack_penalty_weights,
    u_min_physical=u_min_W_m2,
    u_max_physical=u_max_W_m2,
    scalers=scalers,
    margins=margins,
)


start_time = time.time()
mpc_results_df = run_simulation(
    plant=plant,
    warmup_controller=rbc_controller,
    eval_controller=mpc_controller,
    observer=observer,
    config=simulation_config,
    df=controller_input_df,
)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"MPC simulation completed in {elapsed_time:.2f} seconds.")


results = {
    "RBC": rbc_results_df,
    "MPC": mpc_results_df,
}

# filter evaluation steps from results for plotting and performance evaluation
evaluation_results = {
    name: df[df["simulation_phase"] == SimulationPhase.EVALUATION]
    for name, df in results.items()
}
rbc_results_df = evaluation_results["RBC"]
mpc_results_df = evaluation_results["MPC"]


mpc_fig = plot_simulation_results_multiple_controllers(results=evaluation_results)
mpc_fig.show()

# %%
#
# obs_fig = plot_observer_convergence(mpc_results_df)
# obs_fig.show()
#
# %%
#
rbc_performance_results = hvac_control_performance_metrics(rbc_results_df)

rbc_performance_results = pd.concat(
    {"rbc": rbc_performance_results}, names=["experiment_id"]
)
print(rbc_performance_results)

# %%

mpc_performance_results = hvac_control_performance_metrics(mpc_results_df)
mpc_performance_results = pd.concat(
    {"mpc": mpc_performance_results}, names=["experiment_id"]
)
print(mpc_performance_results)
print("Done")

# %%
# Save results to CSV
# test_file = "expected_rbc_simulation_results.parquet"
# rbc_results_df.to_parquet(paths.test_data_dir / test_file)
# rbc_results_df.to_parquet(
#     paths.output_dir / "controller_experiments/rbc/rbc_simulation_results.parquet"
# )
# %%
#
# # Plot Pareto front with Optuna and Plotly, and add RBC point to the plot for comparison
#
# import optuna
# import plotly.graph_objects as go
# from optuna.visualization import plot_pareto_front
#
# study = optuna.load_study(study_name=study_name, storage=f"sqlite:///{optuna_db_path}")
# fig = plot_pareto_front(
#     study,
#     target_names=["Energy Consumption (Watts)", "Comfort Violation (Kelvin hours)"],
#     include_dominated_trials=True,
#     axis_order=None,
#     constraints_func=None,
#     targets=None,
# )
# # Extract RBC objective values using confirmed column names
# rbc_energy = rbc_performance_results.loc["rbc", "total_energy_watt_hour"].item()
# rbc_comfort = rbc_performance_results.loc[
#     "rbc", "total_comfort_violation_kelvin_hours"
# ].item()
#
# fig.add_trace(
#     go.Scatter(
#         x=[rbc_energy],
#         y=[rbc_comfort],
#         mode="markers",
#         name="RBC",
#         showlegend=False,
#         marker=dict(
#             symbol="diamond",
#             size=16,
#             color="#E84545",  # strong but muted red
#             line=dict(
#                 color="white", width=3
#             ),  # white outline separates it from background
#         ),
#     )
# )
# fig.add_annotation(
#     x=rbc_energy,
#     y=rbc_comfort,
#     text="<b>RBC</b>",
#     showarrow=False,
#     yshift=30,
#     xshift=30,
#     font=dict(
#         size=20,
#         color="#E84545",  # matches the marker color
#         family="Inter, Helvetica Neue, Arial, sans-serif",
#     ),
#     bgcolor="rgba(255, 255, 255, 1)",
#     bordercolor="#E84545",  # border matches marker
#     borderwidth=2,
#     borderpad=4,
# )
# fig.update_layout(
#     xaxis=dict(range=[550_000, 700_000]),
#     yaxis=dict(range=[0, 200]),
# )
#
#
# %%
