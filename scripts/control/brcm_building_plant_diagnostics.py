import numpy as np

from alphabuilding import constants as global_config
from alphabuilding.control.brcm_building import BRCMBuildingSimulator
from alphabuilding.control.utils import load_learned_lti_ss
from alphabuilding.domain.types import Scalers

# Test plant cooling rate at controller timestep (15 minutes)
plant = BRCMBuildingSimulator()
plant.reset(initial_temp=20.0)

# No heating, very cold ambient
u_radiators = np.zeros(5)
t_amb = -14.0  # Very cold (corresponds to normalized -3.0)
solar_rad = 0.0

# Plant timestep: 30 seconds
plant_dt_sec = 30
# Controller timestep: 15 minutes = 900 seconds
controller_dt_sec = 15 * 60
# Ratio: number of plant steps per controller step
ratio = int(controller_dt_sec / plant_dt_sec)  # = 30

# Simulate multiple controller timesteps
n_controller_steps = 4  # 1 hour total
temps_over_time = []

for step in range(n_controller_steps + 1):
    temps_over_time.append(plant.x[:5].copy())

    if step < n_controller_steps:  # Don't simulate past the last
        # Run 'ratio' plant steps to complete one controller timestep
        for _ in range(ratio):
            plant.simulate_one_step(u_radiators, t_amb, solar_rad)

# Display results
print("Temperature over 1 hour (15-min controller timesteps):")
for i, t in enumerate(temps_over_time):
    print(f"  t={i * 15}min: {t}")

# Calculate cooling rate per controller timestep
print("\nPer-timestep ΔT (predicted vs actual):")
for i in range(1, len(temps_over_time)):
    dt_actual = temps_over_time[i - 1] - temps_over_time[i]
    print(f"  Step {i}: ΔT = {dt_actual}")

overall_cooling_rate = temps_over_time[0] - temps_over_time[-1]
print(f"\nOverall cooling rate: {overall_cooling_rate} °C/hour")

# Load scalers for conversion
model_path = global_config.CHOSEN_MODEL

sys_learned, dm, _, hydra_cfg = load_learned_lti_ss(
    path=model_path, auto_select_last=False
)

scalers = Scalers(
    temp=dm.zone_temp_scaler,
    amb=dm.ambient_temp_scaler,
    sol=dm.solar_radiation_scaler,
    heat=dm.heat_input_scaler,
)

# Compare to controller prediction (normalized)
predicted_dt_normalized = np.array(
    [0.355, 0.385, 0.402, 0.459, 0.287]
)  # From debug output

# Convert normalized delta to physical units
# For small deltas, physical_delta ≈ normalized_delta * std
physical_delta_approx = predicted_dt_normalized * scalers.temp.base_scaler.scale_
print(f"Controller predicted ΔT per 15 min (normalized): {predicted_dt_normalized}")
print(f"Controller predicted ΔT per 15 min (physical, approx): {physical_delta_approx}")

# Ambient check
normalized_amb = -3.0
physical_amb = scalers.amb.inverse_transform(np.array([normalized_amb]))
print(f"Normalized ambient -3.0 corresponds to physical: {physical_amb[0]:.1f}°C")

# Check model eigenvalues
eigenvalues = np.linalg.eigvals(sys_learned.A)
print(f"\nA matrix eigenvalues (real part): {np.real(eigenvalues)}")
print(f"A matrix eigenvalues (magnitude): {np.abs(eigenvalues)}")
print(f"Max |eigenvalue|: {np.max(np.abs(eigenvalues)):.6f}")

# Check disturbance gains
B_d = sys_learned.B[:, 5:]
print("\nDisturbance gains B_d (ambient & solar influence on temp):")
print(f"  Ambient (B_d[:, 0]): {B_d[:5, 0]}")
print(f"  Solar (B_d[:, 1]): {B_d[:5, 1]}")

# Quick simulation of what model predicts
nx_interal_model = sys_learned.A.shape[0]
x_model = np.full(nx_interal_model, 0.796)  # Current normalized temp (from debug)
u_model = np.zeros(5)  # No control
amb_norm = -3.0
solar_norm = 0.0
d_model = np.array([amb_norm, solar_norm])

x_pred_model = (
    sys_learned.A @ x_model
    + sys_learned.B[:, :5] @ u_model
    + sys_learned.B[:, 5:] @ d_model
)
dt_pred_model = x_model - x_pred_model
print("\nModel prediction for one step:")
print(f"  Start temp: {x_model}")
print(f"  Disturbances: amb={amb_norm}, sol={solar_norm}")
print(f"  Predicted next temp: {x_pred_model}")
print(f"  Predicted ΔT: {dt_pred_model}")
