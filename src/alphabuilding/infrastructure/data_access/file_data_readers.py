from pathlib import Path

import pandas as pd

from alphabuilding.domain.ports import IDataReader


class CsvDataReader(IDataReader):
    """A concrete implementation for reading CSV files."""

    def read(
        self,
        source: Path | str,
        nrows: int | None = None,
        skip_data_rows: int = 0,
        timestamp_col="Datetime",
    ) -> pd.DataFrame:
        """
        Reads data from a CSV file into a pandas DataFrame.

        Args:
            source: The file path to the CSV file.

        Returns:
            A pandas DataFrame with the contents of the CSV.
        """
        # print(f"Reading CSV data from: {source}")
        rows_to_skip = None
        if skip_data_rows > 0:
            rows_to_skip = list(range(1, skip_data_rows + 1))

        return pd.read_csv(
            source,
            header=0,
            nrows=nrows,
            skiprows=rows_to_skip,
            index_col=timestamp_col,
            parse_dates=[timestamp_col],
        )
