import pandas as pd

from alphabuilding import constants as global_config
from alphabuilding.control.performance_metrics import hvac_control_performance_metrics
from alphabuilding.control.types import SimulationPhase
from alphabuilding.control.visualization import (
    plot_observer_convergence,
    plot_simulation_results_multiple_controllers,
)
from alphabuilding.utils.paths import paths

# load parquet files for RBC and MPC results
base_dir = paths.output_dir / "mpc_experiments" / "20260226-141916"
rbc_dir = base_dir / "rbc"
mpc_dir = base_dir / "noise_stds[0, 0]_lamda0_Tmargin2.0_h32_sw100.0000_11411df9"

rbc_results_df = pd.read_parquet(rbc_dir / "results.parquet")
mpc_results_df = pd.read_parquet(mpc_dir / "results.parquet")

results = {
    "RBC": rbc_results_df,
    "MPC": mpc_results_df,
}

# filter evaluation steps from results for plotting and performance evaluation
results = {
    name: df[df["simulation_phase"] == SimulationPhase.EVALUATION]
    for name, df in results.items()
}

# %%

mpc_fig = plot_simulation_results_multiple_controllers(
    results=results, date_fmt="%b-%d %H:%M"
)
mpc_fig.savefig(
    paths.figures_dir / "best_mpc_vs_rbc_trajectories.png",
)

# %%
#
# obs_fig = plot_observer_convergence(rbc_results_df)
# obs_fig.show()
#
# %%
#
# rbc_performance_results = hvac_control_performance_metrics(rbc_results_df)
#
# rbc_performance_results = pd.concat(
#     {"rbc": rbc_performance_results}, names=["experiment_id"]
# )
# rbc_performance_results
#
# mpc_performance_results = hvac_control_performance_metrics(mpc_results_df)
# mpc_performance_results = pd.concat(
#     {"mpc": mpc_performance_results}, names=["experiment_id"]
# )
# mpc_performance_results
#
# %%
# Save results to CSV
# test_file = "expected_rbc_simulation_results.parquet"
# rbc_results_df.to_parquet(paths.test_data_dir / test_file)
# rbc_results_df.to_parquet(
#     paths.output_dir / "controller_experiments/rbc/rbc_simulation_results.parquet"
# )
# %%
