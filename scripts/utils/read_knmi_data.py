from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.conf.paths import paths


def read_knmi_hourly_data(filepath, year):
    """
    Read KNMI hourly weather data and extract temperature for a specific year.

    Parameters:
    -----------
    filepath : str
        Path to the KNMI text file
    year : int
        Year to extract (e.g., 2008, 2021)

    Returns:
    --------
    pandas.DataFrame
        DataFrame with datetime index and 'Outdoor Temp' column at 10-minute resolution, interpolated.
    """

    # Read the file, skip header lines until we find the data
    with open(filepath, "r") as f:
        lines = f.readlines()

    # Find the line starting with '#' that contains column names
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("# STN"):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find header line starting with '# STN'")

    # Parse column names from header
    header_line = lines[header_idx].strip()
    columns = [col.strip() for col in header_line[1:].split(",")]  # Remove leading '#'

    # Read data starting from line after header
    data_lines = lines[header_idx + 1 :]

    # Parse data
    data_rows = []
    for line in data_lines:
        if line.strip():  # Skip empty lines
            values = [val.strip() for val in line.split(",")]
            data_rows.append(values)

    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=columns)

    # Convert YYYYMMDD and HH to datetime
    # Note: HH ranges from 1-24, where hour 1 represents 00:00-01:00 UTC
    # We use the END of the hour for the timestamp
    df["YYYYMMDD"] = df["YYYYMMDD"].astype(str).str.strip()
    df["HH"] = df["HH"].astype(str).str.strip().astype(int)

    # Create datetime: HH=1 means 01:00, HH=24 means 00:00 next day
    df["datetime"] = pd.to_datetime(df["YYYYMMDD"], format="%Y%m%d")
    df["datetime"] = df["datetime"] + pd.to_timedelta(df["HH"], unit="h")

    # Filter for specific year
    df = df[df["datetime"].dt.year == year].copy()

    if len(df) == 0:
        raise ValueError(f"No data found for year {year}")

    # Extract temperature (T column is in 0.1 degrees Celsius)
    df["T"] = df["T"].replace("", np.nan).astype(float)
    df["Outdoor Temp"] = df["T"] / 10.0  # Convert to degrees Celsius

    df["Q"] = df["Q"].replace("", np.nan).astype(float)
    df["Total Radiation"] = df["Q"] * 10000 / 3600  # Convert from J/cm2 to W/m2

    # Set datetime as index
    df = df.set_index("datetime")[["Outdoor Temp", "Total Radiation"]]
    # df = df.set_index("datetime")

    # Sort by datetime
    df = df.sort_index()

    # Resample to 10-minute intervals using linear interpolation
    df_resampled = df.resample("10min").interpolate(method="linear")

    return df_resampled


# Example usage:
if __name__ == "__main__":
    # Specify your file path and year
    data_dir = Path(paths.data_dir)
    filepath = data_dir / "knmi" / "uurgegegevens_Rotterdam_2021-2030.txt"
    year = 2021

    # Process the data
    df = read_knmi_hourly_data(filepath, year)

    # Save to CSV
    save_path = data_dir / "processed"
    output_filepath = save_path / f"knmi_data_{year}_10min.csv"
    df.to_csv(output_filepath)

    print(f"Data saved to {output_filepath}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"Number of records: {len(df)}")
    print("\nFirst few rows:")
    print(df.head(40))
