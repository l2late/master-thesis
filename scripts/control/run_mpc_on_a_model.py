import numpy as np

from alphabuilding import constants as global_config
from alphabuilding.control.brcm_building import (
    BRCMBuildingSimulator,
)
from alphabuilding.control.controllers import (
    EconomicMPCController,
)
from alphabuilding.control.simulation import run_mpc_simulation
from alphabuilding.control.utils import (
    get_controller_input_df,
    load_learned_lti_ss,
)
from alphabuilding.control.visualization import (
    plot_simulation_results_multiple_controllers,
)
from alphabuilding.domain.types import Scalers

# %%

model_path = global_config.CHOSEN_MODEL

brcm_mat_file = global_config.BRCM_MAT_FILE
NP_ROOM_AREAS = np.array(global_config.ROOM_AREAS)
max_rad_power_W = NP_ROOM_AREAS * 50.0
horizon_days = 1
horizon_hours = horizon_days * 24
horizon = horizon_hours * 4  # 3 hours
R_w = 0.0001
slack_w = 10000
mpc_sim_days = 2
mpc_sim_steps = mpc_sim_days * 24 * 4  # 5 days
ckpt = model_path


# Load model with checkpoint
# TODO: what to do with L_learned?
sys_learned, dm, _, hydra_cfg = load_learned_lti_ss(path=ckpt, auto_select_last=False)


def check_model_properties(ss_model):
    """Verify model is dissipative (temperatures decay without input)"""

    # Check eigenvalues of A matrix
    eigenvalues = np.linalg.eigvals(ss_model.A)
    print(f"A matrix eigenvalues (max magnitude): {np.max(np.abs(eigenvalues)):.6f}")

    if np.max(np.abs(eigenvalues)) > 1.0:
        print("⚠️  WARNING: Model is unstable (eigenvalues > 1)")
    elif np.max(np.abs(eigenvalues)) > 0.999:
        print("⚠️  WARNING: Model is near-integrator (eigenvalues ≈ 1)")
    else:
        print("✓ Model is dissipative (stable)")

    # Check B matrix sign (heating should increase temperature)
    B_u = ss_model.B[:, :5]
    if np.all(B_u >= 0):
        print("✓ B_u matrix has correct sign (heating increases temp)")
    else:
        print("⚠️  WARNING: Some B_u entries are negative")

    # Check if disturbances have reasonable effect
    B_d = ss_model.B[:, 5:]
    print(f"B_d (disturbance gains):\n{B_d[:5, :]}")


# check_model_properties(sys_learned)
# %%

controller_input_df = get_controller_input_df(brcm_mat_file, dm)

# Setup scalers
scalers = Scalers(
    temp=dm.zone_temp_scaler,
    amb=dm.ambient_temp_scaler,
    sol=dm.solar_radiation_scaler,
    heat=dm.heat_input_scaler,
)


# Create MPC
mpc = EconomicMPCController(
    model=sys_learned,
    horizon=horizon,
    R_weight=R_w,
    slack_weight=slack_w,
    u_min_physical=np.zeros(5),
    u_max_physical=np.array(max_rad_power_W),
    scalers=scalers,
)

plant = BRCMBuildingSimulator.from_mat_file(brcm_mat_file)

# %%
plant.reset(initial_temp=20.0)
# Run simulation
results_df = run_mpc_simulation(
    plant=plant,
    controller=mpc,
    sim_steps=mpc_sim_steps,
    df=controller_input_df,
    debug=False,
)
# %%

fig = plot_simulation_results_multiple_controllers(
    {"Economic MPC Controller": results_df}
)

# %%
