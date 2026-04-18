from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import TransformerMixin
from sklearn.exceptions import NotFittedError
from sklearn.preprocessing import StandardScaler
from sklearn.utils.validation import check_is_fitted


# frozen dataclass to represent a physical quantity with a name and unit.
# that way we don't need to use the exact same instance everywhere to represent the same physical quantity.
# a frozen dataclass is hashable (automatically implements __eq__ and __hash__) and can be used as a key in dictionaries.
@dataclass(frozen=True)
class PhysicalQuantity:
    name: str
    unit: str

    def __post_init__(self):
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "unit", self.unit.strip())


@dataclass(frozen=True)
class TimeSeries:
    name: str
    physical_quantity: PhysicalQuantity
    series: pd.Series = field(repr=False)

    def __post_init__(self):
        if self.series.index.is_monotonic_increasing is False:
            raise ValueError("Timestamps must be in increasing order.")
        if not isinstance(self.series.index, pd.DatetimeIndex):
            raise TypeError("Timestamps must be a pandas DatetimeIndex.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "series", self.series.copy())

    def __getitem__(self, key) -> "TimeSeries" | Any:
        """
        Return scalar value for single index, TimeSeries for slices.
        Follows pandas convention: single index → scalar, slice → Series.
        """
        result = self.series.iloc[key]

        if isinstance(result, pd.Series):
            # Slice operation - return new TimeSeries
            # copy mutable data
            # share immutable data
            return TimeSeries(
                name=self.name,
                physical_quantity=self.physical_quantity,
                series=result.copy(),
            )
        else:
            # Single index - return scalar value
            return result

    def __getattr__(self, name):
        """Delegate pandas methods to the underlying series."""
        if hasattr(self.series, name):
            attr = getattr(self.series, name)
            if callable(attr):

                def wrapper(*args, **kwargs):
                    result = attr(*args, **kwargs)
                    # If result is a Series, wrap it back in TimeSeries
                    if isinstance(result, pd.Series):
                        return TimeSeries(self.name, self.physical_quantity, result)
                    return result

                return wrapper
            return attr
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    @classmethod
    def from_pandas(
        cls, name: str, physical_quantity: PhysicalQuantity, series: pd.Series
    ) -> "TimeSeries":
        """Creates a TimeSeries instance from a pandas Series."""

        return cls(name=name, physical_quantity=physical_quantity, series=series.copy())

    @property
    def values(self) -> np.ndarray:
        """Returns a copy of the values to ensure immutability."""
        return self.series.values

    @property
    def timestamps(self) -> pd.DatetimeIndex:
        """Returns the timestamps. DatetimeIndex is immutable."""
        return self.series.index

    def to_pandas(self) -> pd.Series:
        """Reconstructs and returns the pandas Series object."""
        return self.series.copy()

    def __len__(self) -> int:
        """Returns the length of the TimeSeries."""
        return len(self.series)


@dataclass(frozen=True)
class FeatureGroup:
    name: str
    physical_quantity: PhysicalQuantity
    # scaler: TransformerMixin = field(default_factory=MinMaxScaler)
    scaler: TransformerMixin = field(default_factory=StandardScaler)
    timeseries: tuple[TimeSeries, ...] = field(default_factory=tuple)

    def __post_init__(self):
        """Initializes a cache for the concatenated NumPy array."""
        # This allows us to have a mutable cache on a frozen object.
        object.__setattr__(self, "_values_cache", None)

    @property
    def values(self) -> np.ndarray:
        """
        Returns the feature group's data as a single, cached NumPy array.

        The first time this property is accessed, it computes the array by
        stacking all TimeSeries values. Subsequent calls return the cached array,
        avoiding repeated, expensive computation.
        """
        # If the cache is not populated, compute and store the array.
        if self._values_cache is None:
            # Directly stack the .values from each TimeSeries, which are already NumPy arrays.
            # This is far more efficient than building a DataFrame.
            stacked_values = np.stack(
                [ts.series.values for ts in self.timeseries], axis=1
            )
            # Store the result in the cache.
            object.__setattr__(self, "_values_cache", stacked_values)

        return self._values_cache

    def __getitem__(self, key: int | slice) -> "FeatureGroup | pd.Series":
        """
        Returns a pd.Series for a single timestamp lookup, or a new
        FeatureGroup for a time-based slice.

        When slicing, the new FeatureGroup shares the physical_quantity and scaler
        (including its fitted state) with the original, only creating new sliced
        TimeSeries objects.
        """
        if not self.timeseries:
            raise ValueError("FeatureGroup must contain at least one TimeSeries.")
        if isinstance(key, int):
            if key < 0 or key >= len(self):
                raise IndexError("Index out of bounds.")
            else:
                key = slice(key, key + 1)
        if key.start is None or key.stop is None:
            raise IndexError("Slice must have both start and stop defined.")
        if key.start >= key.stop:
            raise IndexError("Slice start must be less than slice stop.")
        if key.start < 0 or key.stop > len(self):
            raise IndexError("Slice indices are out of bounds.")

        test_slice_result = self.timeseries[0].series[key]

        if isinstance(test_slice_result, pd.Series):
            new_timeseries = tuple(ts[key] for ts in self.timeseries)
            return replace(self, timeseries=new_timeseries)
        else:
            return self.to_dataframe().loc[key]

    def __len__(self) -> int:
        """Returns the length of the first TimeSeries in the FeatureGroup."""
        if not self.timeseries:
            return 0
        return len(self.timeseries[0].values)

    @property
    def num_features(self) -> int:
        return len(self.timeseries)

    def add_scaler(self, scaler_instance: TransformerMixin) -> "FeatureGroup":
        return replace(self, scaler=scaler_instance)

    def fit_scaler(self) -> None:
        """Fits the scaler to the values of all TimeSeries in the FeatureGroup."""
        if self.scaler_is_fitted:
            raise ValueError("Scaler is already fitted.")
        if not self.timeseries:
            raise ValueError("No TimeSeries available to fit the scaler.")
        if not self.scaler:
            raise ValueError("Scaler is not set.")

        all_values = np.concatenate([ts.values for ts in self.timeseries]).reshape(
            -1, 1
        )
        assert all_values.ndim == 2, "All values must be 2-dimensional."
        assert all_values.shape[1] == 1, "All values must be single-dimensional."
        self.scaler.fit(all_values)

    @property
    def scaler_is_fitted(self) -> bool:
        """Checks if the scaler is fitted."""
        if not self.scaler:
            return False

        try:
            check_is_fitted(self.scaler)
            return True
        except NotFittedError:
            return False

    @classmethod
    def from_dataframe(
        cls,
        name: str,
        physical_quantity: PhysicalQuantity,
        df: pd.DataFrame,
    ):
        ts_list = []
        for column in df.columns:
            ts = TimeSeries.from_pandas(
                name=column,
                physical_quantity=physical_quantity,
                series=df[column],
            )
            ts_list.append(ts)

        return cls(
            name=name,
            physical_quantity=physical_quantity,
            timeseries=tuple(ts_list),
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Converts the FeatureGroup back to a pandas DataFrame."""
        data = {ts.name: ts.to_pandas() for ts in self.timeseries}
        return pd.DataFrame(data, index=self.timestamps.copy())

    @property
    def timestamps(self) -> pd.DatetimeIndex:
        """Returns the timestamps of the first TimeSeries in the FeatureGroup."""
        if not self.timeseries:
            return pd.DatetimeIndex([])
        return self.timeseries[0].timestamps


class Dataset:
    def __init__(
        self,
        feature_groups: list[FeatureGroup],
    ):
        self.feature_groups = feature_groups
        if not self.feature_groups:
            raise ValueError("Dataset must contain at least one FeatureGroup.")
        lengths = {len(fg) for fg in self.feature_groups}
        if len(lengths) > 1:
            raise ValueError(
                "All FeatureGroups in the Dataset must have the same length."
            )

    def __len__(self) -> int:
        """Returns the length of the first FeatureGroup."""
        if not self.feature_groups:
            return 0
        return len(self.feature_groups[0])

    def get_feature_group(self, name):
        fgs = [fg for fg in self.feature_groups if fg.name == name]
        assert len(fgs) == 1, f"FeatureGroup with name '{name}' not found."
        return fgs[0]

    def get_feature_groups_with_physical_quantity(
        self, physical_quantity: PhysicalQuantity
    ) -> list[FeatureGroup]:
        fgs = [
            fg
            for fg in self.feature_groups
            if fg.physical_quantity == physical_quantity
        ]
        return fgs

    def __getitem__(self, key: int | slice) -> "Dataset":
        if isinstance(key, int):
            key = slice(key, key + 1)
        if key.start is None or key.stop is None:
            raise IndexError("Slice must have both start and stop defined.")
        if key.start < 0 or key.stop > len(self):
            raise IndexError("Slice indices are out of bounds.")
        sliced_feature_groups = [fg[key] for fg in self.feature_groups]
        sliced_ds = Dataset(feature_groups=sliced_feature_groups)
        return sliced_ds

    @property
    def num_feature_groups(self) -> int:
        """Returns the number of FeatureGroups in the Dataset."""
        return len(self.feature_groups)

    @property
    def num_features(self) -> int:
        """Returns the total number of features across all FeatureGroups."""
        return sum(fg.num_features for fg in self.feature_groups)

    @property
    def timestamps(self) -> pd.DatetimeIndex:
        """Returns the timestamps of the first FeatureGroup."""
        if not self.feature_groups:
            return pd.DatetimeIndex([])
        return self.feature_groups[0].timestamps

    def get_timestamps(self, start_idx: int, end_idx: int) -> pd.DatetimeIndex:
        """
        Returns the timestamps for the specified range of indices.
        Assumes all FeatureGroups have the same timestamps.
        """
        if not self.feature_groups:
            raise ValueError("Dataset has no FeatureGroups.")
        if start_idx < 0 or end_idx > len(self):
            raise IndexError("Index out of bounds.")

        return self.feature_groups[0].timestamps[start_idx:end_idx]

    def get_scaled_window(self, start_idx: int, end_idx: int) -> dict[str, np.ndarray]:
        """
        Extracts a window of data, returning a dictionary mapping each
        feature group's name to its scaled NumPy array.
        """
        windows = {}

        for fg in self.feature_groups:
            full_group_values = fg.values
            window_values = full_group_values[start_idx:end_idx]
            scaled_values = self._scale_array(window_values, fg.scaler)
            windows[fg.name] = scaled_values

        return windows

    def get_future_window(self, start: int, horizon: int) -> np.ndarray:
        end = start + horizon
        return self.get_scaled_window(start, end)

    def get_past_window(self, start: int, window: int):
        return self.get_scaled_window(start - window, start)

    def _scale_array(self, data: np.array, scaler: TransformerMixin):
        original_shape = data.shape
        values_to_transform = data.reshape(-1, 1)
        scaled_flat_values = scaler.transform(values_to_transform)
        scaled_values = scaled_flat_values.reshape(original_shape)
        return scaled_values

    def split(
        self,
        train_ratio: float,
        val_ratio: float | None = None,
        test_ratio: float | None = None,
    ) -> tuple["Dataset", ...]:
        ratios = (train_ratio, val_ratio, test_ratio)
        if self._split_ratios_are_invalid(ratios):
            raise ValueError(
                "Ratios must be non-negative and sum to 1 if all are provided."
            )
        splits_to_return = []
        train_end = int(len(self) * train_ratio)
        train_slice = slice(0, train_end)
        train_split = self[train_slice]
        splits_to_return.append(train_split)
        self._fit_scalers(train_split)

        if val_ratio:
            val_start = train_end
            val_length = int(len(self) * val_ratio)
            val_end = val_start + val_length
            val_slice = slice(val_start, val_end)
            val_split = self[val_slice]
            splits_to_return.append(val_split)

        if test_ratio:
            test_start = train_end if val_ratio is None else val_end
            test_length = int(len(self) * test_ratio)
            test_slice = slice(test_start, test_start + test_length)
            test_split = self[test_slice]
            splits_to_return.append(test_split)

        if len(splits_to_return) == 1:
            return splits_to_return[0]  # Return single split if only one exists
        else:
            return tuple(splits_to_return)

    def _splits_are_empty(
        self, ratios: tuple[float, float | None, float | None]
    ) -> bool:
        for r in ratios:
            if r is not None and (len(self) * r) < 1:
                return True
        return False

    def _split_ratios_are_invalid(
        self, ratios: tuple[float, float | None, float | None]
    ) -> bool:
        if self._splits_are_empty(ratios):
            return True
        for r in ratios:
            if r is None or (0 <= r < 1):
                continue
            else:
                return True
        total = sum(r for r in ratios if r is not None)
        if total > 1 or total <= 0:
            return True

    @property
    def scalers(self) -> dict[PhysicalQuantity, TransformerMixin]:
        """Returns a dictionary of scalers for each PhysicalQuantity."""
        scalers = {}
        for fg in self.feature_groups:
            if fg.scaler and fg.physical_quantity not in scalers:
                scalers[fg.physical_quantity] = fg.scaler
        return scalers

    @property
    def scalers_are_fitted(self) -> bool:
        """Checks if all scalers in the Dataset are fitted."""
        return all(fg.scaler_is_fitted for fg in self.feature_groups)

    def _fit_scalers(self, train_dataset: "Dataset | None" = None) -> None:
        """Fits the scalers of each FeatureGroup on the TRAINING split of the Dataset.

        Feature groups with the same physical quantity will share the same scaler instance.
        """
        assert train_dataset is not None, "train_dataset must be provided."

        # Group feature groups by physical quantity
        pq_to_fgs: dict[PhysicalQuantity, list[FeatureGroup]] = {}
        for fg in train_dataset.feature_groups:
            if fg.physical_quantity not in pq_to_fgs:
                pq_to_fgs[fg.physical_quantity] = []
            pq_to_fgs[fg.physical_quantity].append(fg)

        # For each physical quantity, fit one scaler on all data and share it
        for pq, fgs in pq_to_fgs.items():
            # Collect all values from all feature groups with this physical quantity
            all_values_list = []
            for fg in fgs:
                for ts in fg.timeseries:
                    all_values_list.append(ts.values)

            # Concatenate and fit a single scaler
            all_values = np.concatenate(all_values_list).reshape(-1, 1)
            # shared_scaler = MinMaxScaler(feature_range=(0.1, 0.9))
            shared_scaler = StandardScaler()
            shared_scaler.fit(all_values)

            # Update all feature groups (in train, val, test) to use this shared scaler
            # We need to update feature groups in self (the original dataset), not just train_dataset
            for fg in self.feature_groups:
                if fg.physical_quantity == pq:
                    # Use replace to create a new feature group with the shared scaler
                    idx = self.feature_groups.index(fg)
                    self.feature_groups[idx] = replace(fg, scaler=shared_scaler)

            # Also update the splits that have already been created
            for fg in train_dataset.feature_groups:
                if fg.physical_quantity == pq:
                    idx = train_dataset.feature_groups.index(fg)
                    train_dataset.feature_groups[idx] = replace(
                        fg, scaler=shared_scaler
                    )
