from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from alphabuilding.domain.entities import Dataset, FeatureGroup, PhysicalQuantity
from alphabuilding.infrastructure.data_access.file_data_readers import CsvDataReader

COLUMN_MAP = {
    "ZoneMeanAirTemperature 1": PhysicalQuantity("Temperature", "Celsius"),
    "ZoneMeanAirTemperature 2": PhysicalQuantity("Temperature", "Celsius"),
    "ZoneMeanAirTemperature 3": PhysicalQuantity("Temperature", "Celsius"),
    "ZoneMeanAirTemperature 4": PhysicalQuantity("Temperature", "Celsius"),
    "ZoneMeanAirTemperature 5": PhysicalQuantity("Temperature", "Celsius"),
    "Environment": PhysicalQuantity("Temperature", "Celsius"),
    "HeatInput 1": PhysicalQuantity("Heat Input", "Watt"),
    "HeatInput 2": PhysicalQuantity("Heat Input", "Watt"),
    "HeatInput 3": PhysicalQuantity("Heat Input", "Watt"),
    "HeatInput 4": PhysicalQuantity("Heat Input", "Watt"),
    "HeatInput 5": PhysicalQuantity("Heat Input", "Watt"),
    "Total Solar Radiation": PhysicalQuantity("Solar Radiation", "Watt/m2"),
}

SCALING_STRATEGY = {
    PhysicalQuantity("Temperature", "Celsius"): StandardScaler(),
    PhysicalQuantity("Heat Input", "Watt"): StandardScaler(),
    PhysicalQuantity("Solar Radiation", "Watt"): StandardScaler(),
}


class BRCMDatasetCreationService:
    """Service to create a BRCM dataset from a CSV file."""

    def create_dataframe(
        self, csv_file: Path, skip_data_rows: int = 0, nrows: int | None = None
    ) -> pd.DataFrame:
        """Creates a pandas DataFrame from the CSV file."""
        reader = CsvDataReader()
        df = reader.read(source=csv_file, skip_data_rows=skip_data_rows, nrows=nrows)
        return df

    def create_dataset(
        self,
        csv_file: Path,
        skip_data_rows: int = 0,
        nrows: int | None = None,
        # noise_std_temp: float = 0.0,
        # noise_std_solar_rad: float = 0.0,
    ) -> Dataset:
        """Creates a BRCM dataset from the CSV file.
        Optionally adds Gaussian noise to the temperature (Zone and Ambient) and solar radiation features.
        """
        df = self.create_dataframe(
            csv_file=csv_file, skip_data_rows=skip_data_rows, nrows=nrows
        )

        # if noise_std_temp > 0.0:
        #     temp_cols = df.filter(regex="ZoneMeanAirTemperature|Environment").columns
        #
        #     noise = np.random.normal(
        #         loc=0.0, scale=noise_std_temp, size=df[temp_cols].shape
        #     )
        #     df[temp_cols] += noise
        #
        # if noise_std_solar_rad > 0.0:
        #     rad_cols = df.filter(regex="Total Solar Radiation").columns
        #
        #     noise = np.random.normal(
        #         loc=0.0, scale=noise_std_solar_rad, size=df[rad_cols].shape
        #     )
        #
        #     # clip to 0 to prevent unphysical negative radiation
        #     df[rad_cols] = (df[rad_cols] + noise).clip(lower=0.0)

        zone_temps_df = df.filter(regex="ZoneMeanAirTemperature")
        temp_pq = PhysicalQuantity("Temperature", "Celsius")
        fg_zone_temps = FeatureGroup.from_dataframe(
            name="zone_temps", physical_quantity=temp_pq, df=zone_temps_df
        )

        ambient_temp_df = df.filter(regex="Environment")
        fg_ambient_temp = FeatureGroup.from_dataframe(
            name="ambient_temp", physical_quantity=temp_pq, df=ambient_temp_df
        )

        heat_inputs_df = df.filter(regex="HeatInput")
        heat_pq = PhysicalQuantity("Heat Input", "Watt")
        fg_heat_inputs = FeatureGroup.from_dataframe(
            name="heat_input", physical_quantity=heat_pq, df=heat_inputs_df
        )

        solar_rad_df = df.filter(regex="Solar Radiation")
        solar_rad_pq = PhysicalQuantity("Solar Radiation", "Watt/m2")
        fg_solar_rad = FeatureGroup.from_dataframe(
            name="solar_radiation", physical_quantity=solar_rad_pq, df=solar_rad_df
        )

        feature_groups = [fg_ambient_temp, fg_zone_temps, fg_heat_inputs, fg_solar_rad]

        return Dataset(feature_groups=feature_groups)
