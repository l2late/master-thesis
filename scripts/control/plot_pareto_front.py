import pandas as pd

from alphabuilding.control.performance_metrics import hvac_control_performance_metrics
from alphabuilding.control.results import ControllerSimulationComparator
from alphabuilding.control.types import SimulationPhase
from alphabuilding.control.utils import (
    parallel_load_experiment_bundle,
)
from alphabuilding.control.visualization import (
    plot_simulation_results_multiple_controllers,
)
from alphabuilding.utils.paths import get_latest_mpc_sweep_run_dir, paths

# %%

# mpc_experiments_dir = get_latest_mpc_sweep_run_dir()
mpc_experiments_dir = paths.output_dir / "mpc_experiments" / "20260226-141916"

# rbc_experiments_dir = mpc_experiments_dir / "rbc"
# assert rbc_experiments_dir.exists(), (
#     f"RBC experiments directory not found: {rbc_experiments_dir}"
# )
# rbc_results = pd.read_parquet(
#     rbc_experiments_dir / "results.parquet",
#     filters=[("simulation_phase", "==", SimulationPhase.EVALUATION)],
# )
rbc_results = None

# %%

limit = None
all_mpc_experiments_df = parallel_load_experiment_bundle(
    root=mpc_experiments_dir,
    limit=limit,
    filter_simulation_phase=SimulationPhase.EVALUATION,
    filter_Tmargin=1,
    filter_lambda_reg=0,
)

# %%

# rbc_performance_metrics = hvac_control_performance_metrics(rbc_results)

control_results = ControllerSimulationComparator(
    mpc_results=all_mpc_experiments_df,
    reference_results=rbc_results,
    strict=True,
    simulation_phase=SimulationPhase.EVALUATION,
)
mpc_pareto_data = control_results._compute_mpc_pareto_front()

# %%
all_mpc_experiments_df.index.levels[0].unique()
mpc_pareto_data


# %%
control_results.pareto_plot()
print("Done")
