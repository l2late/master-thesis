import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from alphabuilding.domain.entities import Dataset, FeatureGroup
from tests.fixtures.factories import make_feature_group, make_physical_quantity


def make_dataset(len_timeseries=5):
    pq1 = make_physical_quantity(name="Temperature", unit="Celsius")
    pq2 = make_physical_quantity(name="Radiator Heat Input", unit="Watt")
    fg1 = make_feature_group(
        name="Zone Temperature",
        physical_quantity=pq1,
        num_timeseries=2,
        length=len_timeseries,
    )
    fg2 = make_feature_group(
        name="Radiator Heat Input",
        physical_quantity=pq2,
        num_timeseries=2,
        length=len_timeseries,
    )
    # different group, same physical quantity
    fg3 = make_feature_group(
        name="Ambient Temperature",
        physical_quantity=pq1,
        num_timeseries=1,
        length=len_timeseries,
    )
    feature_groups = [fg1, fg2, fg3]
    dataset = Dataset(feature_groups=feature_groups)
    return dataset


@pytest.fixture
def train_dataset():
    dataset = make_dataset(len_timeseries=1000)
    train_dataset, _, _ = dataset.split(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)
    return train_dataset


def test_dataset_constructor():
    dataset = make_dataset()
    assert isinstance(dataset, Dataset), "Should create a Dataset instance"


def test_dataset_length():
    dataset = make_dataset(len_timeseries=5)
    assert len(dataset) == 5, "Dataset should contain two FeatureGroups"


def test_empty_dataset_fails():
    with pytest.raises(ValueError):
        _ = Dataset(feature_groups=[])


def test_dataset_with_feature_groups_of_different_lengths_fails():
    fg1 = make_feature_group(length=5)
    fg2 = make_feature_group(length=10)
    with pytest.raises(ValueError):
        _ = Dataset(feature_groups=[fg1, fg2])


def test_getitem_with_single_index_returns_dataset():
    dataset = make_dataset(len_timeseries=10)
    idx = 1
    result = dataset[idx]
    assert isinstance(result, Dataset)


def test_getitem_with_single_index_out_of_range_fails():
    dataset = make_dataset(len_timeseries=10)
    idx = 100
    with pytest.raises(IndexError):
        _ = dataset[idx]


def test_getitem_with_slice_out_of_range_fails():
    dataset = make_dataset(len_timeseries=10)
    start = 10
    length = 15
    end = start + length
    with pytest.raises(IndexError):
        _ = dataset[slice(start, end)]


def test_train_split():
    dataset = make_dataset(len_timeseries=10)
    train_dataset = dataset.split(train_ratio=0.6)
    assert len(train_dataset) == 6


def test_train_and_val_split():
    dataset = make_dataset(len_timeseries=10)
    train_dataset, val_dataset = dataset.split(train_ratio=0.6, val_ratio=0.4)
    assert len(train_dataset) == 6
    assert len(val_dataset) == 4


def test_train_val_and_test_split():
    dataset = make_dataset(len_timeseries=10)
    train_dataset, val_dataset, test_dataset = dataset.split(
        train_ratio=0.6, val_ratio=0.2, test_ratio=0.2
    )
    assert len(train_dataset) == 6
    assert len(val_dataset) == 2
    assert len(test_dataset) == 2


def test_ratios_smaller_than_zero_fails():
    dataset = make_dataset(len_timeseries=2)
    with pytest.raises(ValueError):
        dataset.split(train_ratio=-0.1)


def test_train_ratio_larger_than_one_fails():
    dataset = make_dataset(len_timeseries=2)
    with pytest.raises(ValueError):
        _ = dataset.split(train_ratio=1.2)


def test_sum_ratios_larger_than_one_fail():
    dataset = make_dataset(len_timeseries=2)
    with pytest.raises(ValueError):
        _ = dataset.split(train_ratio=0.6, val_ratio=0.5)
    with pytest.raises(ValueError):
        _ = dataset.split(train_ratio=0.6, val_ratio=0.3, test_ratio=0.2)


def test_sum_ratios_zero_fails():
    dataset = make_dataset(len_timeseries=2)
    with pytest.raises(ValueError):
        _ = dataset.split(train_ratio=0, val_ratio=0, test_ratio=0)
    with pytest.raises(ValueError):
        _ = dataset.split(train_ratio=0)


def test_train_split_ratio_leads_to_dataset_with_length_less_than_1():
    dataset = make_dataset(len_timeseries=2)
    with pytest.raises(ValueError):
        _ = dataset.split(train_ratio=0.3)


def test_val_split_ratio_leads_to_dataset_with_length_less_than_1():
    dataset = make_dataset(len_timeseries=2)
    with pytest.raises(ValueError):
        _ = dataset.split(train_ratio=0.5, val_ratio=0.4)


def test_test_split_ratio_leads_to_dataset_with_length_less_than_1():
    dataset = make_dataset(len_timeseries=10)
    with pytest.raises(ValueError):
        _ = dataset.split(train_ratio=0.5, val_ratio=0.45, test_ratio=0.05)


def test_dataset_has_scalers():
    dataset = make_dataset(len_timeseries=2)
    assert hasattr(dataset, "scalers")


def test_scalers_are_fitted_after_splitting():
    dataset = make_dataset(len_timeseries=10)
    splits = dataset.split(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)
    for split in splits:
        assert split.scalers_are_fitted


def test_train_scalers_are_equal_to_val_scalers():
    dataset = make_dataset(len_timeseries=10)
    train_dataset, val_dataset = dataset.split(train_ratio=0.6, val_ratio=0.4)
    assert train_dataset.scalers == val_dataset.scalers


def test_train_scalers_are_equal_to_val_and_test_scalers():
    dataset = make_dataset(len_timeseries=10)
    train_dataset, val_dataset, test_dataset = dataset.split(
        train_ratio=0.6, val_ratio=0.2, test_ratio=0.2
    )
    assert train_dataset.scalers == val_dataset.scalers
    assert train_dataset.scalers == test_dataset.scalers


def test_fitted_scaler_returns_only_values_between_0_and_1_for_train_split():
    dataset = make_dataset(len_timeseries=1000)
    train_dataset, _, _ = dataset.split(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)
    for fg in train_dataset.feature_groups:
        for ts in fg.timeseries:
            training_data = ts.values
            assert np.all(np.min(training_data) >= 0.0)
            assert np.all(np.max(training_data) <= 1.0)


def test_num_feature_groups():
    dataset = make_dataset(len_timeseries=2)
    assert dataset.num_feature_groups == 3


def test_num_features():
    dataset = make_dataset(len_timeseries=2)
    assert dataset.num_features == 5


def test_get_timestamps_has_right_length(train_dataset):
    start = 0
    length = 500
    end = start + length
    timestamps = train_dataset.get_timestamps(start, end)
    assert len(timestamps) == length, (
        "Timestamps should have the same length as the window"
    )
    assert isinstance(timestamps, pd.DatetimeIndex)
    assert isinstance(timestamps[0].to_numpy(), np.datetime64)


def test_get_scaled_window_dict_is_right_shape(train_dataset):
    start = 0
    length = 500
    end = start + length
    window_dict = train_dataset.get_scaled_window(start, end)
    assert isinstance(window_dict, dict)
    assert window_dict["Zone Temperature"].shape == (length, 2)
    assert window_dict["Radiator Heat Input"].shape == (length, 2)


def test_get_future_window(train_dataset):
    start = 10
    horizon = 6
    end = start + horizon
    expected_window = train_dataset.get_scaled_window(start, end)
    future_window = train_dataset.get_future_window(start=10, horizon=6)
    for key, array in future_window.items():
        assert future_window[key].shape == expected_window[key].shape
        assert np.array_equal(array, expected_window[key])


def test_get_past_window(train_dataset):
    # start and end get reversed : takes past values relative to present
    start = 10
    window = 6
    expected_window = train_dataset.get_scaled_window(start - window, start)
    past_window = train_dataset.get_past_window(start=10, window=6)
    for key, array in past_window.items():
        assert past_window[key].shape == expected_window[key].shape
        assert np.array_equal(array, expected_window[key])


def test_get_feature_group(train_dataset):
    zone_temps_fg = train_dataset.get_feature_group("Zone Temperature")
    assert isinstance(zone_temps_fg, FeatureGroup)
    radiator_fg = train_dataset.get_feature_group("Radiator Heat Input")
    assert isinstance(radiator_fg, FeatureGroup)


def test_feature_ambient_and_zone_temperatures_have_same_physical_quantity(
    train_dataset,
):
    zone_temps_fg = train_dataset.get_feature_group("Zone Temperature")
    ambient_temp_fg = train_dataset.get_feature_group("Ambient Temperature")
    assert zone_temps_fg.physical_quantity == ambient_temp_fg.physical_quantity


def test_feature_groups_with_same_physical_quantity_have_same_scaler(train_dataset):
    zone_temps_fg = train_dataset.get_feature_group("Zone Temperature")
    ambient_temp_fg = train_dataset.get_feature_group("Ambient Temperature")
    assert zone_temps_fg.scaler == ambient_temp_fg.scaler


def test_feature_groups_with_same_physical_quantity_share_scaler_across_all_splits():
    dataset = make_dataset(len_timeseries=1000)
    train_dataset, val_dataset, test_dataset = dataset.split(
        train_ratio=0.6, val_ratio=0.2, test_ratio=0.2
    )

    train_zone = train_dataset.get_feature_group("Zone Temperature")
    train_ambient = train_dataset.get_feature_group("Ambient Temperature")
    val_zone = val_dataset.get_feature_group("Zone Temperature")
    val_ambient = val_dataset.get_feature_group("Ambient Temperature")
    test_zone = test_dataset.get_feature_group("Zone Temperature")
    test_ambient = test_dataset.get_feature_group("Ambient Temperature")

    assert train_zone.scaler is train_ambient.scaler
    assert train_zone.scaler is val_zone.scaler
    assert train_zone.scaler is val_ambient.scaler
    assert train_zone.scaler is test_zone.scaler
    assert train_zone.scaler is test_ambient.scaler


def test_shared_scaler_is_fitted_on_all_data_from_same_physical_quantity():
    dataset = make_dataset(len_timeseries=1000)
    train_dataset, _, _ = dataset.split(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)

    zone_temps_fg = train_dataset.get_feature_group("Zone Temperature")
    ambient_temp_fg = train_dataset.get_feature_group("Ambient Temperature")

    scaler = zone_temps_fg.scaler
    if isinstance(scaler, MinMaxScaler):
        min_val = scaler.data_min_[0]
        max_val = scaler.data_max_[0]

        all_temp_values = []
        for ts in zone_temps_fg.timeseries:
            all_temp_values.extend(ts.values)
        for ts in ambient_temp_fg.timeseries:
            all_temp_values.extend(ts.values)

        assert np.isclose(min_val, np.min(all_temp_values), rtol=1e-5)
        assert np.isclose(max_val, np.max(all_temp_values), rtol=1e-5)

    if isinstance(scaler, StandardScaler):
        mean_val = scaler.mean_[0]
        scale_val = scaler.scale_[0]

        all_temp_values = []
        for ts in zone_temps_fg.timeseries:
            all_temp_values.extend(ts.values)
        for ts in ambient_temp_fg.timeseries:
            all_temp_values.extend(ts.values)

        assert np.isclose(mean_val, np.mean(all_temp_values), rtol=1e-5)
        assert np.isclose(scale_val, np.std(all_temp_values), rtol=1e-5)

    else:
        pytest.fail("Scaler is neither MinMaxScaler nor StandardScaler")


def test_feature_groups_with_different_physical_quantities_have_different_scalers(
    train_dataset,
):
    zone_temps_fg = train_dataset.get_feature_group("Zone Temperature")
    radiator_fg = train_dataset.get_feature_group("Radiator Heat Input")

    assert zone_temps_fg.scaler is not radiator_fg.scaler


def test_scaler_sharing_with_three_feature_groups_same_physical_quantity():
    pq_temp = make_physical_quantity(name="Temperature", unit="Celsius")
    fg1 = make_feature_group(
        "Zone 1 Temp", physical_quantity=pq_temp, num_timeseries=1, length=100
    )
    fg2 = make_feature_group(
        "Zone 2 Temp", physical_quantity=pq_temp, num_timeseries=1, length=100
    )
    fg3 = make_feature_group(
        "Ambient Temp", physical_quantity=pq_temp, num_timeseries=1, length=100
    )

    dataset = Dataset(feature_groups=[fg1, fg2, fg3])
    train, val = dataset.split(train_ratio=0.7, val_ratio=0.3)

    train_fg1 = train.get_feature_group("Zone 1 Temp")
    train_fg2 = train.get_feature_group("Zone 2 Temp")
    train_fg3 = train.get_feature_group("Ambient Temp")

    assert train_fg1.scaler is train_fg2.scaler
    assert train_fg1.scaler is train_fg3.scaler


def test_shared_scaler_parameters_are_identical(train_dataset):
    zone_temps_fg = train_dataset.get_feature_group("Zone Temperature")
    ambient_temp_fg = train_dataset.get_feature_group("Ambient Temperature")

    zone_temps_scaler = zone_temps_fg.scaler
    ambient_temp_scaler = ambient_temp_fg.scaler
    if not isinstance(zone_temps_scaler, type(ambient_temp_scaler)):
        pytest.fail("Scalers are of different types")
    if isinstance(zone_temps_scaler, StandardScaler):
        assert np.array_equal(zone_temps_fg.scaler.mean_, ambient_temp_fg.scaler.mean_)
        assert np.array_equal(
            zone_temps_fg.scaler.scale_, ambient_temp_fg.scaler.scale_
        )
    elif isinstance(zone_temps_scaler, MinMaxScaler):
        assert np.array_equal(
            zone_temps_fg.scaler.data_min_, ambient_temp_fg.scaler.data_min_
        )
        assert np.array_equal(
            zone_temps_fg.scaler.data_max_, ambient_temp_fg.scaler.data_max_
        )
        assert np.array_equal(
            zone_temps_fg.scaler.scale_, ambient_temp_fg.scaler.scale_
        )


def test_dataset_scalers_property_returns_one_scaler_per_physical_quantity(
    train_dataset,
):
    scalers = train_dataset.scalers

    assert len(scalers) == 2

    pq_temp = train_dataset.get_feature_group("Zone Temperature").physical_quantity
    pq_heat = train_dataset.get_feature_group("Radiator Heat Input").physical_quantity

    assert pq_temp in scalers
    assert pq_heat in scalers


def test_scaler_sharing_with_single_feature_group_per_physical_quantity():
    pq1 = make_physical_quantity(name="Temperature", unit="Celsius")
    pq2 = make_physical_quantity(name="Power", unit="Watt")
    fg1 = make_feature_group("Zone Temp", physical_quantity=pq1, length=100)
    fg2 = make_feature_group("Heater Power", physical_quantity=pq2, length=100)

    dataset = Dataset(feature_groups=[fg1, fg2])
    train, val = dataset.split(train_ratio=0.7, val_ratio=0.3)

    assert train.scalers_are_fitted
    assert val.scalers_are_fitted


def test_get_all_feature_groups_with_same_physical_quantity(train_dataset):
    temp_pq = make_physical_quantity(name="Temperature", unit="Celsius")
    heat_pq = make_physical_quantity(name="Radiator Heat Input", unit="Watt")
    temperature_fgs = train_dataset.get_feature_groups_with_physical_quantity(temp_pq)
    heat_fgs = train_dataset.get_feature_groups_with_physical_quantity(heat_pq)
    assert isinstance(temperature_fgs, list)
    assert len(temperature_fgs) == 2
    assert all(fg.physical_quantity == temp_pq for fg in temperature_fgs), (
        "All feature groups should have the Temperature physical quantity"
    )
    assert isinstance(heat_fgs, list)
    assert len(heat_fgs) == 1
    assert all(fg.physical_quantity == heat_pq for fg in heat_fgs), (
        "All feature groups should have the Radiator Heat Input physical quantity"
    )


##### TEST LIST #####
# test get all feature groups with a specific physical quantity (usefull for adding same type of noise)
