from dataclasses import dataclass, fields
from enum import Enum
from typing import NamedTuple, Protocol, runtime_checkable

import numpy as np
import torch
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler


class GraphTopology(str, Enum):
    # These are the different types of graph topologies we can use for the A matrix in our model.
    UNCONSTRAINED = "unconstrained"
    PHYSICAL_FULLY_CONNECTED = "fully-connected"
    PHYSICAL_ONE_TO_ONE = "1-to-1"
    PHYSICAL_ONE_TO_MANY = "1-to-many"
    FULLY_CONNECTED_ONE_TO_ONE = "fully-connected-1-to-1"

    @classmethod
    def _missing_(cls, value):
        # Fallback: try matching by member name
        try:
            return cls[value]
        except KeyError:
            return None


class TrajectoryBatch(NamedTuple):
    # Past Trajectories (Inputs to Observer/Encoder)
    past_ambient_temp: torch.Tensor
    past_zone_temps: torch.Tensor
    past_heat_inputs: torch.Tensor
    past_solar_rad: torch.Tensor

    # Future Trajectories (Inputs to Dynamics/Decoder)
    future_ambient_temp: torch.Tensor
    future_heat_inputs: torch.Tensor
    future_zone_temps: torch.Tensor
    future_solar_rad: torch.Tensor

    # timestamps, useful for debugging and plotting
    past_timestamps: torch.Tensor
    future_timestamps: torch.Tensor


class InitialStateEstimate(NamedTuple):
    x0: torch.Tensor
    observer_traj: torch.Tensor | None
    innovation_traj: torch.Tensor | None
    something: int = 0  # :[ don't know what this is currently. probably for inference


@runtime_checkable
class Scaler(Protocol):
    """Protocol matching sklearn-style scalers (StandardScaler, MinMaxScaler, etc.)"""

    def fit(self, *args, **kwargs): ...
    def transform(self, X: np.ndarray) -> np.ndarray: ...
    def inverse_transform(self, X: np.ndarray) -> np.ndarray: ...


@dataclass
class Scalers:
    temp: Scaler  # Zone temperature scaler
    amb: Scaler  # NOTE: this is the same scaler as temp as they have the same units (PhysicalQuantity) of temperature in °C
    sol: Scaler  # solar radiation scaler
    heat: Scaler  # heat input scaler

    def __post_init__(self):
        """
        Automatically wraps any sklearn-style scalers in SharedScaler
        to ensure they handle ND arrays correctly.
        """
        for field in fields(self):
            scaler = getattr(self, field.name)

            # Check if it needs wrapping (is a valid scaler but NOT yet a SharedScaler)
            # We check hasattr(scaler, 'transform') to ensure it's scaler-like
            if (
                scaler
                and not isinstance(scaler, SharedScaler)
                and hasattr(scaler, "transform")
            ):
                # Replace the raw sklearn scaler with the wrapped version
                wrapped_scaler = SharedScaler(scaler)
                setattr(self, field.name, wrapped_scaler)


class SharedScaler(BaseEstimator, TransformerMixin):
    """
    Wraps an sklearn scaler to apply the same scaling
    to every element of an input array, regardless of shape.
    """

    def __init__(self, base_scaler: Scaler | None = None):
        self.base_scaler = base_scaler or StandardScaler()

    def fit(self, X, y=None):
        # Flatten all data to (N, 1) to learn a single mean/std
        # for the entire dataset
        self.base_scaler.fit(X.reshape(-1, 1), y)
        return self

    def transform(self, X):
        original_shape = X.shape
        X_flat = X.reshape(-1, 1)
        X_scaled = self.base_scaler.transform(X_flat)
        return X_scaled.reshape(original_shape)

    def inverse_transform(self, X):
        original_shape = X.shape
        X_flat = X.reshape(-1, 1)
        X_inv = self.base_scaler.inverse_transform(X_flat)
        return X_inv.reshape(original_shape)


@runtime_checkable
class Controller(Protocol):
    """Protocol for the MPC controller"""

    def solve(
        self,
        x0: np.ndarray,
        disturbance_forecast: np.ndarray,
        T_min_future: np.ndarray,
        T_max_future: np.ndarray,
    ) -> np.ndarray: ...
