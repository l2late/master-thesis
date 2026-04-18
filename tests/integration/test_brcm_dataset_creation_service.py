import pytest

from application.services.brcm_dataset_creation_service import (
    BRCMDatasetCreationService,
)
from domain.entities import Dataset, PhysicalQuantity


# TODO: refactor fixture to use the "in-memory" csv. see conftest.py for details
@pytest.fixture
def brcm_dataset_100(five_room_csv):
    service = BRCMDatasetCreationService()
    return service.create_dataset(csv_file=five_room_csv, nrows=100)


@pytest.fixture
def noisy_brcm_dataset_100(five_room_csv):
    service = BRCMDatasetCreationService()
    return service.create_dataset(
        csv_file=five_room_csv, nrows=100, noise_std_temp=0.5, noise_std_solar_rad=1.0
    )


def test_brcm_dataset_creation_service_with_limited_rows(brcm_dataset_100):
    dataset = brcm_dataset_100
    assert isinstance(dataset, Dataset)

    assert len(dataset) == 100
    assert len(dataset.feature_groups) == 4
    assert len(dataset.feature_groups[0]) == 100

    train_dataset, val_dataset, test_dataset = dataset.split(
        train_ratio=0.7, val_ratio=0.2, test_ratio=0.1
    )
    assert len(train_dataset) == 70
    assert len(val_dataset) == 20
    assert len(test_dataset) == 10


def test_brcm_dataset_creation_service_with_noise_has_non_negative_solar_radiation(
    noisy_brcm_dataset_100,
):
    dataset = noisy_brcm_dataset_100
    solar_radiation_fg = dataset.get_feature_group("solar_radiation")
    assert (solar_radiation_fg.values >= 0).all()


def test_brcm_dataset_creation_service_with_noise_alters_temperature_and_solar_rad_values(
    brcm_dataset_100,
    noisy_brcm_dataset_100,
):
    clean_dataset = brcm_dataset_100
    noisy_dataset = noisy_brcm_dataset_100

    temp_pq = PhysicalQuantity("Temperature", "Celsius")
    sol_rad_pq = PhysicalQuantity("Solar Radiation", "Watt")

    pqs = [temp_pq, sol_rad_pq]  # physical quantities that should be noised

    for pq in pqs:
        clean_fgs_list = clean_dataset.get_feature_groups_with_physical_quantity(pq)
        noisy_fgs_list = noisy_dataset.get_feature_groups_with_physical_quantity(pq)

        for clean_fg, noisy_fg in zip(clean_fgs_list, noisy_fgs_list):
            print(f"Checking physical quantity: {pq.name}")
            assert clean_fg.values.shape == noisy_fg.values.shape, "Shapes do not match"
            assert not (clean_fg.values == noisy_fg.values).all(), (
                f"Some or all values are identical for physical quantity {pq.name}"
            )


def test_brcm_dataset_creation_service_with_noise_does_not_alter_heat_input_values(
    brcm_dataset_100,
    noisy_brcm_dataset_100,
):
    clean_dataset = brcm_dataset_100
    noisy_dataset = noisy_brcm_dataset_100

    heat_pq = PhysicalQuantity("Heat Input", "Watt")

    clean_heat_fgs = clean_dataset.get_feature_groups_with_physical_quantity(heat_pq)
    noisy_heat_fgs = noisy_dataset.get_feature_groups_with_physical_quantity(heat_pq)

    for clean_fg, noisy_fg in zip(clean_heat_fgs, noisy_heat_fgs):
        assert clean_fg.values.shape == noisy_fg.values.shape, "Shapes do not match"
        assert (clean_fg.values == noisy_fg.values).all(), (
            "Heat input values should not be altered by noise addition"
        )
