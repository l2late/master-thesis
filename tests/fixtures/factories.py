import uuid

import numpy as np
import pandas as pd
import torch

from alphabuilding.constants import Levels
from alphabuilding.domain.entities import FeatureGroup, PhysicalQuantity, TimeSeries

N_ROOMS = 5


def make_dataframe(num_rows=10, num_timeseries=1):
    """Creates a sample timeindex DataFrame with random data."""
    data = np.random.rand(num_rows, num_timeseries)
    timestamps = pd.date_range(start="2023-01-01", periods=num_rows, freq="h")
    columns = [f"Value {i + 1}" for i in range(num_timeseries)]
    df = pd.DataFrame(data, index=timestamps, columns=columns)
    return df


def make_physical_quantity(name="Temperature", unit="Celsius"):
    return PhysicalQuantity(name=name, unit=unit)


def make_timeseries(physical_quantity=None, length=10, start_time=None, value=1.0):
    pq = physical_quantity or make_physical_quantity()
    start = start_time or np.datetime64("2002-09-09")
    timestamps = np.array([start + np.timedelta64(i, "h") for i in range(length)])
    values = np.full(length, value, dtype=float)
    pd_series = pd.Series(values, index=pd.DatetimeIndex(timestamps))

    return TimeSeries.from_pandas(
        name=f"TimeSeries {uuid.uuid4()}",
        physical_quantity=pq,
        series=pd_series,
    )


def make_feature_group(
    name: str = "some_name", physical_quantity=None, num_timeseries=1, length=10
):
    df = make_dataframe(num_rows=length, num_timeseries=num_timeseries)
    pq = physical_quantity or make_physical_quantity()
    fg = FeatureGroup.from_dataframe(name=name, physical_quantity=pq, df=df)
    return fg


def make_batch(batch_size, num_rooms, window_size, horizon, device="cpu"):
    past_zone_temps = torch.rand(batch_size, window_size, num_rooms)
    past_heat_input = torch.rand(batch_size, window_size, num_rooms)
    past_ambient_temp = torch.rand(batch_size, window_size, 1)
    past_timestamps = torch.arange(start=0, end=window_size, dtype=torch.int64).repeat(
        batch_size, 1
    )

    # horizon + 1 because it also contains t0
    future_zone_temps = torch.rand(batch_size, horizon + 1, num_rooms)
    future_heat_input = torch.rand(batch_size, horizon + 1, num_rooms)
    future_ambient_temp = torch.rand(batch_size, horizon + 1, 1)
    future_timestamps = torch.arange(
        start=window_size - 1, end=window_size + horizon, dtype=torch.int64
    ).repeat(batch_size, 1)

    batch = {
        # Past data (history)
        "past_zone_temps_traj": past_zone_temps,
        "past_heat_input_traj": past_heat_input,
        "past_ambient_temp_traj": past_ambient_temp,
        "measurement_traj_timestamps": past_timestamps,
        # Future data (for prediction and as target)
        "future_zone_temps_traj": future_zone_temps,
        "future_heat_input_traj": future_heat_input,
        "future_ambient_temp_traj": future_ambient_temp,
        "target_traj_timestamps": future_timestamps,
    }

    if device != "cpu":
        for key in batch:
            batch[key] = batch[key].to(device)

    return batch


def make_simulation_result(
    length=5,
    frequency="30s",
    u_value=100,
    y_value=22.0,
    Tmin=20.0,
    Tmax=24.0,
):
    index = pd.date_range(start="2024-01-01", periods=length, freq=frequency)
    u_cols = {f"u{i + 1}": [u_value] * length for i in range(N_ROOMS)}
    y_cols = {f"y{i + 1}": [y_value] * length for i in range(N_ROOMS)}
    data = {
        **u_cols,
        **y_cols,
        "Tmin": [Tmin] * length,
        "Tmax": [Tmax] * length,
        "Tamb": 10.0,
        "SolRad": 400.0,
    }
    df = pd.DataFrame(data, index=index)
    df.index.name = "datetime"
    return df


def concat_simulation_results(
    results_dict: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Args:
        results_dict: Dict mapping experiment_id -> simulation result DataFrame

    Returns:
        MultiIndex DataFrame with Levels.experiment and Levels.datetime
    """
    frames = []
    keys = []

    for exp_id, df in results_dict.items():
        frames.append(df)
        keys.append(exp_id)

    return pd.concat(
        frames, keys=keys, names=[Levels.experiment, Levels.datetime]
    ).assign(
        horizon=24,
        lambda_reg_eigvals=0.1,
        Tmargin=1,
        R_weight=1,
        SolRad_std=0.0,
        Tamb_std=0.0,
        slack_weight=1.0,
    )
