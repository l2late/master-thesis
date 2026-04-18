import numpy as np
import pandas as pd
import pandera.pandas as pa
from pandera.typing import Index


# 2. Base Schema (15 min frequency)
class ControllerInput(pa.DataFrameModel):
    # We define the field with the 15-minute check
    datetime: Index[pa.DateTime]

    Tamb: float
    SolRad: float

    Tmin: float
    Tmax: float

    class Config:
        strict = True  # Ban extra columns
        coerce = True  # Auto-convert types if possible

    @pa.check("datetime", name="frequency_check")
    def check_frequency(cls, idx: Index[pa.DateTime]) -> bool:
        """Enforce 15-minute frequency using fast numpy operations."""
        # Convert to numpy array of nanoseconds (int64)
        # This is essentially zero-copy for datetime64[ns]
        timestamps = idx.values.astype(np.int64)

        # Calculate diffs in nanoseconds
        diffs = np.diff(timestamps)

        # 15 minutes in nanoseconds = 15 * 60 * 1e9 = 900,000,000,000
        # or use pd.Timedelta("15min").value
        expected_ns = pd.Timedelta("15min").value

        # Check if ALL diffs equal the expected value
        return np.all(diffs == expected_ns)

    @pa.dataframe_check(
        error="Tmax must be strictly greater than Tmin at every timestep"
    )
    @classmethod
    def check_tmin_less_than_tmax(cls, df: pd.DataFrame) -> pd.Series:
        return df["Tmax"] > df["Tmin"]

    @pa.dataframe_check(
        error="Comfort band must be >= 2°C wide. This is just a sanity check. Change it if you know what you are doing."
    )
    @classmethod
    def check_comfort_band_width(cls, df: pd.DataFrame) -> pd.Series:
        return (df["Tmax"] - df["Tmin"]) >= 2


class PlantInput(ControllerInput):
    u1: float
    u2: float
    u3: float
    u4: float
    u5: float

    class Config:
        strict = True  # Ban extra columns
        coerce = True  # Auto-convert types if possible

    @pa.check("datetime", name="frequency_check")
    def check_frequency(cls, idx: Index[pa.DateTime]) -> bool:
        """Enforce 30-second frequency (Optimized)."""
        timestamps = idx.values.astype(np.int64)
        diffs = np.diff(timestamps)

        expected_ns = pd.Timedelta("30s").value
        return np.all(diffs == expected_ns)


# Define the schema for simulation output
class SimulationResult(PlantInput):
    y1: float
    y2: float
    y3: float
    y4: float
    y5: float

    class Config:
        strict = False  # Ban extra columns
        coerce = True  # Auto-convert types if possible


class MpcSimulationResult(SimulationResult):
    horizon: int
    slack_weight: float
    R_weight: float
    Tamb_std: float
    SolRad_std: float
    lambda_reg_eigvals: float
    Tmargin: float

    class Config:
        strict = False  # Ban extra columns
        coerce = True  # Auto-convert types if possible
