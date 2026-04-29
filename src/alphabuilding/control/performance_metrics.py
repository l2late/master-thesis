import numpy as np
import pandas as pd

from alphabuilding.control.types import SimulationPhase
from alphabuilding.domain.df_schemas import SimulationResult


def compute_single_controller_simulation_performance_metrics(
    df: SimulationResult,
) -> pd.DataFrame:
    # 1. Determine Sampling Time (dt) in hours
    # We take the difference between the first two timestamps of the first experiment
    dt_seconds = (df.index[1] - df.index[0]).total_seconds()
    dt_hours = dt_seconds / 3600.0

    # 2. Vectorized Pre-calculation
    # Calculate total instantaneous power (sum of u1..u5)
    # u_cols = ["u1", "u2", "u3", "u4", "u5"]
    # df["power_instant_sum"] = df[u_cols].sum(axis=1)

    # Calculate instantaneous violations for all zones
    y_cols = ["y1", "y2", "y3", "y4", "y5"]
    y_vals = df[y_cols].values
    tmin_vals = df["Tmin"].values[:, None]
    tmax_vals = df["Tmax"].values[:, None]

    # Violation = max(0, Tmin - y) + max(0, y - Tmax)
    # This shape is (N_rows, 5_zones)
    viol_matrix = np.maximum(0, tmin_vals - y_vals) + np.maximum(0, y_vals - tmax_vals)

    # Sum of violations across all rooms and all time
    df["Kelvin_hour_sum"] = viol_matrix.sum(axis=1).sum() * dt_hours
    # df["Kelvin_hour_max"] = viol_matrix.max(axis=1)  # Worst violation across all rooms

    # df["total_energy_watt_hour"] = df["power_instant_sum"] * dt_hours
    # df["total_kelvin_hour"] = df["violation_instant_sum"] * dt_hours
    return df


def total_comfort_violation_kelvin_hours(df: pd.DataFrame) -> float:
    assert len(df) >= 2, (
        "DataFrame must have at least two rows to determine sampling time."
    )
    dt_seconds = (df.index[1] - df.index[0]).total_seconds()
    dt_hours = dt_seconds / 3600.0

    # 2. Vectorized Pre-calculation
    y_cols = ["y1", "y2", "y3", "y4", "y5"]
    y_vals = df[y_cols].values
    tmin_vals = df["Tmin"].values[:, None]
    tmax_vals = df["Tmax"].values[:, None]

    # Violation = max(0, Tmin - y) + max(0, y - Tmax)
    viol_matrix = np.maximum(0, tmin_vals - y_vals) + np.maximum(0, y_vals - tmax_vals)

    # Sum of violations across all rooms and all time
    total_kelvin_hours = viol_matrix.sum(axis=1).sum() * dt_hours
    return total_kelvin_hours


def total_energy_consumption_watt_hour(df: pd.DataFrame) -> float:
    assert len(df) >= 2, (
        "DataFrame must have at least two rows to determine sampling time."
    )
    dt_seconds = (df.index[1] - df.index[0]).total_seconds()
    dt_hours = dt_seconds / 3600.0

    # 2. Vectorized Pre-calculation
    u_cols = ["u1", "u2", "u3", "u4", "u5"]
    power_instant_sum = df[u_cols].sum(axis=1)

    # Total energy consumption in watt-hours
    total_energy_wh = power_instant_sum.sum() * dt_hours
    return total_energy_wh


def max_power_consumption_watt(df: pd.DataFrame) -> float:
    u_cols = ["u1", "u2", "u3", "u4", "u5"]
    power_instant_sum = df[u_cols].sum(axis=1)
    max_power_watt = power_instant_sum.max()
    return float(max_power_watt)


def hvac_control_performance_metrics(
    df: pd.DataFrame, phase: SimulationPhase = SimulationPhase.EVALUATION
) -> pd.DataFrame:
    df = df[df["simulation_phase"] == phase.value]
    total_energy = total_energy_consumption_watt_hour(df)
    total_violation = total_comfort_violation_kelvin_hours(df)
    max_power = max_power_consumption_watt(df)

    result_df = pd.DataFrame(
        {
            "total_energy_watt_hour": [total_energy],
            "total_comfort_violation_kelvin_hours": [total_violation],
            "max_power_consumption_watt": [max_power],
        }
    )
    return result_df
