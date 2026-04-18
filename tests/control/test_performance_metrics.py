import pandas as pd
import pytest

from alphabuilding.control.performance_metrics import (
    hvac_control_performance_metrics,
    max_power_consumption_watt,
    total_comfort_violation_kelvin_hours,
    total_energy_consumption_watt_hour,
)
from tests.fixtures.factories import make_simulation_result

N_ROOMS = 5


@pytest.mark.parametrize(
    "y_value,Tmin,Tmax,length,frequency",
    [
        (22.0, 20.0, 24.0, 10, "1h"),  # No violation
        (25.0, 20.0, 24.0, 10, "1h"),  # 1K over
        (19.0, 20.0, 24.0, 10, "1h"),  # 1K under
        (19.0, 20.0, 24.0, 2, "30min"),  # 30min intervals
        (18.0, 20.0, 24.0, 4, "15min"),  # Multiple variations
    ],
)
def test_total_kelvin_hours_violation_explicit(y_value, Tmin, Tmax, length, frequency):
    df = make_simulation_result(
        length=length,
        frequency=frequency,
        y_value=y_value,
        Tmin=Tmin,
        Tmax=Tmax,
    )

    # Calculate expected value explicitly in test
    violation_per_room = max(0, y_value - Tmax, Tmin - y_value)
    hours = pd.Timedelta(frequency) * length / pd.Timedelta("1h")
    expected = violation_per_room * hours * N_ROOMS

    result = total_comfort_violation_kelvin_hours(df)
    assert result == pytest.approx(expected)


def test_empty_dataframe_raises_error():
    df = make_simulation_result(length=0)
    with pytest.raises(AssertionError):
        total_comfort_violation_kelvin_hours(df)


def test_dataframe_with_1_measurements_raises_error():
    df = make_simulation_result(length=1)
    with pytest.raises(AssertionError):
        total_comfort_violation_kelvin_hours(df)


@pytest.mark.parametrize(
    "u_value,Tmin,Tmax,length,frequency",
    [
        (100.0, 20.0, 24.0, 10, "1h"),  # No violation
        (10.0, 20.0, 24.0, 10, "1h"),  # 1K over
        (0.0, 20.0, 24.0, 10, "1h"),  # 1K under
        (0.0, 20.0, 24.0, 2, "30min"),  # 30min intervals
        (0.0, 20.0, 24.0, 4, "15min"),  # Multiple variations
    ],
)
def test_total_energy_consumption(u_value, Tmin, Tmax, length, frequency):
    df = make_simulation_result(
        u_value=u_value, Tmin=Tmin, Tmax=Tmax, length=length, frequency=frequency
    )
    hours = pd.Timedelta(frequency) * length / pd.Timedelta("1h")
    expected = u_value * hours * N_ROOMS
    actual_energy_consumed = total_energy_consumption_watt_hour(df)
    assert actual_energy_consumed == pytest.approx(expected)


def test_max_power_consumption_watt():
    df = make_simulation_result(length=5, frequency="1h", u_value=100)
    expected = 100 * N_ROOMS
    actual = max_power_consumption_watt(df)
    assert actual == pytest.approx(expected)


def test_control_performance_metrics():
    df = make_simulation_result(
        length=10, frequency="1h", u_value=150, y_value=26.0, Tmin=20.0, Tmax=24.0
    )
    expected_total_energy = 150.0 * 10 * N_ROOMS
    expected_total_violation = 2.0 * 10 * N_ROOMS
    expected_max_power = 150.0 * N_ROOMS
    expected_df = pd.DataFrame(
        {
            "total_energy_watt_hour": [expected_total_energy],
            "total_comfort_violation_kelvin_hours": [expected_total_violation],
            "max_power_consumption_watt": [expected_max_power],
        }
    )
    actual_df = hvac_control_performance_metrics(df)
    pd.testing.assert_frame_equal(actual_df, expected_df)
