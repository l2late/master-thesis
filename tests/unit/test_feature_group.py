import pandas as pd
import pytest
from sklearn.preprocessing import MinMaxScaler

from alphabuilding.domain.entities import FeatureGroup, TimeSeries
from tests.fixtures.factories import make_physical_quantity


@pytest.fixture()
def empty_fg():
    """Fixture to create an empty FeatureGroup."""
    pq = make_physical_quantity()
    name = "empty_feature_group"
    return FeatureGroup(name=name, physical_quantity=pq)


@pytest.fixture()
def feature_group_with_1_timeseries():
    name = "empty_feature_group"
    data_dict = {
        "value": [1.0, 2.0, 3.0],
        "timestamp": pd.date_range(start="2023-01-01", periods=3, freq="D"),
    }
    df = pd.DataFrame(data_dict).set_index("timestamp")
    pq = make_physical_quantity()
    return FeatureGroup.from_dataframe(name=name, physical_quantity=pq, df=df)


@pytest.fixture()
def feature_group_with_2_timeseries():
    name = "empty_feature_group"
    data_dict = {
        "value1": [1.0, 2.0, 3.0],
        "value2": [4.0, 5.0, 6.0],
        "timestamp": pd.date_range(start="2023-01-01", periods=3, freq="D"),
    }
    df = pd.DataFrame(data_dict).set_index("timestamp")
    pq = make_physical_quantity()
    return FeatureGroup.from_dataframe(name=name, physical_quantity=pq, df=df)


def test_single_index_out_of_bounds_raises_error(feature_group_with_1_timeseries):
    fg = feature_group_with_1_timeseries
    with pytest.raises(IndexError):
        _ = fg[10]


def test_slice_index_entirely_out_of_bounds_raises_error(
    feature_group_with_1_timeseries,
):
    fg = feature_group_with_1_timeseries
    with pytest.raises(IndexError):
        _ = fg[4:6]


def test_slice_index_partly_out_of_bounds_raises_error(
    feature_group_with_1_timeseries,
):
    fg = feature_group_with_1_timeseries
    with pytest.raises(IndexError):
        _ = fg[2:4]


def test_constructor_from_pandas_dataframe(feature_group_with_1_timeseries):
    for ts in feature_group_with_1_timeseries.timeseries:
        assert isinstance(ts, TimeSeries), "Should create TimeSeries from DataFrame"


def test_constructor_from_pandas_dataframe_with_2_cols(feature_group_with_2_timeseries):
    for ts in feature_group_with_2_timeseries.timeseries:
        assert isinstance(ts, TimeSeries), "Should create TimeSeries from DataFrame"


def test_GivenFeatureGroupWithoutTimeseries_WhenFitScaler_thenRaiseError(empty_fg):
    with pytest.raises(ValueError, match="No TimeSeries available to fit the scaler"):
        _ = empty_fg.fit_scaler()


def test_fit_scaler_then_scaler_fitted(feature_group_with_1_timeseries):
    fg = feature_group_with_1_timeseries.add_scaler(MinMaxScaler())
    fg.fit_scaler()
    assert fg.scaler_is_fitted, "Scaler should be fitted after calling fit_scaler"


def test_scale_fg_with_2_ts(feature_group_with_2_timeseries):
    fg = feature_group_with_2_timeseries.add_scaler(MinMaxScaler())
    fg.fit_scaler()
    assert fg.scaler_is_fitted, "Scaler should be fitted after calling fit_scaler"


def test_feature_group_length(
    feature_group_with_1_timeseries,
    feature_group_with_2_timeseries,
):
    assert len(feature_group_with_1_timeseries) == 3, (
        "FeatureGroup should contain 3 rows"
    )
    assert len(feature_group_with_2_timeseries) == 3, (
        "FeatureGroup should contain 3 rows"
    )


def test_to_dataframe():
    name = "feature_group"
    data_dict = {
        "value1": [1.0, 2.0, 3.0],
        "value2": [4.0, 5.0, 6.0],
        "timestamp": pd.date_range(start="2023-01-01", periods=3, freq="D"),
    }
    original_df = pd.DataFrame(data_dict).set_index("timestamp")
    pq = make_physical_quantity()
    fg = FeatureGroup.from_dataframe(name=name, physical_quantity=pq, df=original_df)
    constructed_df = fg.to_dataframe()
    assert isinstance(constructed_df, pd.DataFrame), "Should return a DataFrame"
    assert original_df.equals(constructed_df), (
        "DataFrame should match original DataFrame"
    )


def test_feature_group_access_by_slice_returns_row_vector():
    name = "feature_group"
    data_dict = {
        "value1": [1.0, 2.0, 3.0],
        "value2": [4.0, 5.0, 6.0],
        "timestamp": pd.date_range(start="2023-01-01", periods=3, freq="D"),
    }
    df = pd.DataFrame(data_dict).set_index("timestamp")
    pq = make_physical_quantity()
    fg = FeatureGroup.from_dataframe(name=name, physical_quantity=pq, df=df)
    slice_idx = slice(1, 2)
    sliced_fg = fg[slice_idx]
    actual_df = sliced_fg.to_dataframe()
    expected_df = df[slice_idx]
    assert actual_df.equals(expected_df)
    assert isinstance(sliced_fg, FeatureGroup), "Should return a FeatureGroup"
    assert sliced_fg.physical_quantity == fg.physical_quantity, (
        "Physical quantity should match original FeatureGroup"
    )


def test_slicing_maintains_reference_to_original_scaler(
    feature_group_with_1_timeseries,
):
    fg = feature_group_with_1_timeseries
    sliced_fg = fg[0:1]
    assert fg.scaler == sliced_fg.scaler


def test_slicing_feature_group_returns_new_fg(feature_group_with_1_timeseries):
    fg = feature_group_with_1_timeseries
    sliced_fg = fg[0:1]
    assert isinstance(sliced_fg, FeatureGroup), "Slicing should return a FeatureGroup"
    assert len(sliced_fg) == 1, "Sliced FeatureGroup should have one row"
    assert sliced_fg.physical_quantity == fg.physical_quantity, (
        "Physical quantity should match original FeatureGroup"
    )


def test_scaler_is_fitted_after_fit(feature_group_with_1_timeseries):
    fg = feature_group_with_1_timeseries
    fg.fit_scaler()
    assert fg.scaler_is_fitted


def test_scaler_is_not_fitted_before_fit(feature_group_with_1_timeseries):
    fg = feature_group_with_1_timeseries
    assert not fg.scaler_is_fitted


def test_num_features(feature_group_with_1_timeseries, feature_group_with_2_timeseries):
    assert feature_group_with_1_timeseries.num_features == 1
    assert feature_group_with_2_timeseries.num_features == 2
