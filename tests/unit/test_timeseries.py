import numpy as np
import pandas as pd
import pytest

from alphabuilding.domain.entities import PhysicalQuantity, TimeSeries


@pytest.fixture
def temperature_quantity() -> PhysicalQuantity:
    """A valid PhysicalQuantity value object for temperature."""
    return PhysicalQuantity(name="Temperature", unit="Celsius")


@pytest.fixture
def valid_timestamps() -> np.ndarray:
    """A valid, monotonic array of timestamps."""
    start = np.datetime64("2025-07-28T10:00:00")
    return np.array(
        [start, start + np.timedelta64(1, "m"), start + np.timedelta64(2, "m")]
    )


@pytest.fixture
def valid_values() -> np.ndarray:
    """A valid array of finite float values."""
    return np.array([22.1, 22.3, 22.2])


@pytest.fixture
def pd_series() -> pd.Series:
    index = pd.date_range("2025-07-28 10:00:00", periods=3, freq="min")
    values = [22.1, 22.3, 22.2]
    pd_series = pd.Series(values, index=index)
    return pd_series


def test_timeseries_from_pandas(pd_series, temperature_quantity):
    """Test creating a TimeSeries from a pandas Series."""
    ts = TimeSeries.from_pandas(
        name="Temperature Room 1",
        physical_quantity=temperature_quantity,
        series=pd_series,
    )
    assert isinstance(ts, TimeSeries)
    assert ts.name == "Temperature Room 1"
    assert ts.physical_quantity == temperature_quantity
    assert np.array_equal(ts.values, pd_series.values)
    assert ts.timestamps.equals(pd_series.index)


def test_timeseries_name_has_no_leading_nor_trailing_whitespaces(pd_series):
    """Test that TimeSeries name has no leading or trailing whitespaces."""
    pq = PhysicalQuantity(name="Temperature", unit="Celsius")
    ts = TimeSeries.from_pandas(
        name=" Temperature Room 1 ",
        physical_quantity=pq,
        series=pd_series,
    )
    assert ts.name == "Temperature Room 1"


def test_timeseries_values_is_np_array(temperature_quantity, pd_series):
    ts = TimeSeries.from_pandas(
        name="Temperature Room 1",
        physical_quantity=temperature_quantity,
        series=pd_series,
    )
    assert isinstance(ts.values, np.ndarray)


def test_timeseries_timestamps_is_datetime_index(temperature_quantity, pd_series):
    ts = TimeSeries.from_pandas(
        name="Temperature Room 1",
        physical_quantity=temperature_quantity,
        series=pd_series,
    )
    assert isinstance(ts.timestamps, pd.DatetimeIndex)


def test_timeseries_values_are_immutable(temperature_quantity):
    index = pd.date_range("2025-07-28 10:00:00", periods=3, freq="min")
    values = [22.1, 22.3, 22.2]
    pd_series = pd.Series(values, index=index)
    ts = TimeSeries.from_pandas(
        name="Temperature Room 1",
        physical_quantity=temperature_quantity,
        series=pd_series,
    )
    pd_series.values[0] = 1
    assert np.array_equal(ts.values, np.array(values))


def test_timeseries_timestamps_are_immutable(temperature_quantity):
    index = pd.date_range("2025-07-28 10:00:00", periods=3, freq="min")
    values = [22.1, 22.3, 22.2]
    pd_series = pd.Series(values, index=index)
    ts = TimeSeries.from_pandas(
        name="Temperature Room 1",
        physical_quantity=temperature_quantity,
        series=pd_series,
    )
    with pytest.raises(TypeError):
        ts.timestamps[0] = np.datetime64("2025-07-28 10:00:00")


def test_timeseries_timestamps_must_be_monotonic_increasing(temperature_quantity):
    index = pd.DatetimeIndex(
        [
            np.datetime64("2025-07-28 10:00:00"),
            np.datetime64("2025-07-28 10:20:00"),
            np.datetime64("2025-07-28 10:10:00"),
        ]
    )
    values = [22.1, 22.3, 22.2]
    pd_series = pd.Series(values, index=index)
    with pytest.raises(ValueError, match="Timestamps must be in increasing order."):
        _ = TimeSeries.from_pandas(
            name="Temperature Room 1",
            physical_quantity=temperature_quantity,
            series=pd_series,
        )


def test_timeseries_access_by_index(temperature_quantity, pd_series):
    ts = TimeSeries.from_pandas(
        name="Temperature Room 1",
        physical_quantity=temperature_quantity,
        series=pd_series,
    )
    idx = 1
    scalar = ts[idx]
    assert not isinstance(scalar, TimeSeries)
    assert np.equal(scalar, pd_series.iloc[idx])


def test_timeseries_access_by_slice(temperature_quantity, pd_series):
    ts = TimeSeries.from_pandas(
        name="Temperature Room 1",
        physical_quantity=temperature_quantity,
        series=pd_series,
    )
    idx_slice = slice(1, 3)
    single_ts = ts[idx_slice]
    assert isinstance(single_ts, TimeSeries)
    assert single_ts.name == "Temperature Room 1"
    assert single_ts.physical_quantity == temperature_quantity
    assert np.array_equal(single_ts.values, pd_series.values[idx_slice])
    assert single_ts.timestamps.equals(pd_series.index[idx_slice])
