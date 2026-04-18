from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class IDataReader(ABC):
    """
    Interface defining a contract for reading data from a source
    and returning it as a pandas DataFrame.

    This abstraction decouples the application's core logic from the
    specifics of data retrieval (e.g., file format, database type).
    """

    @abstractmethod
    def read(
        self,
        source: Path | str,
        nrows: int | None,
        skip_data_rows: int,
        timestamp_col=str,
    ) -> pd.DataFrame:
        """
        Reads data from a given source.

        Args:
            source: The identifier for the data source, such as a
                    file path or a database connection string.

        Returns:
            A pandas DataFrame containing the data.
        """
        ...
