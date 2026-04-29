from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path

import lightning as L
import numpy as np
import pandas as pd
import scipy
import torch

from alphabuilding import constants as global_config

torch.set_grad_enabled(False)

ROOM_AREAS = global_config.ROOM_AREAS


class TimeDomain(str, Enum):
    """Temporal domain of a dynamical system."""

    CONTINUOUS = "continuous"
    DISCRETE = "discrete"

    @property
    def requires_sample_time(self) -> bool:
        return self == TimeDomain.DISCRETE


class DisturbanceIdx(IntEnum):
    # check the Matlab BRCM code for exact ordering
    IG1 = 2  # internal gain
    IG2 = 4
    IG3 = 3
    IG4 = 1
    IG5 = 0
    T_AMB = 5
    T_GROUND = 6
    SOLAR_EAST = 7
    SOLAR_NORTH = 8
    SOLAR_SOUTH = 9


class ControlIdx(IntEnum):
    # check the Matlab BRCM code for exact ordering
    AHU_NO_ERC = 0
    AHU_HEATER = 1
    AHU_COOLER = 2
    RADIATOR1 = 3
    RADIATOR2 = 4
    RADIATOR3 = 5
    RADIATOR4 = 6
    RADIATOR5 = 7


@dataclass
class BRCMStateSpaceModel:
    A: np.ndarray  # state matrix
    Bu: np.ndarray  # control input matrix
    Bd: np.ndarray  # disturbance input matrix
    # Bdu: np.ndarray  # bilinear control-disturbance matrix
    # Bxu: np.ndarray  # bilinear state-control matrix
    nx: int  # number of states
    nd: int = 2  # number of disturbances (ambient temp and solar radiation)
    nu: int = 5  # number of control inputs (radiator inputs for 5 rooms)
    time_domain: TimeDomain = TimeDomain.CONTINUOUS


def read_brcm_ss_mat_file(mat_file_path: str | Path) -> BRCMStateSpaceModel:
    assert Path(mat_file_path).exists(), f"File not found: {mat_file_path}"
    data = scipy.io.loadmat(mat_file_path)
    ss = BRCMStateSpaceModel(
        A=data["A_cont"],
        Bu=data["Bu_cont"],
        Bd=data["Bv_cont"],
        # Bdu=data["Bvu_cont"],
        # Bxu=data["Bxu_cont"],
        nx=data["A_cont"].shape[0],
        nu=data["Bu_cont"].shape[1],
        nd=data["Bv_cont"].shape[1],
    )

    return ss


def read_mat_file(mat_file_path: str | Path) -> dict[str, np.ndarray]:
    """Utility function that reads .mat file and returns a dictionary of numpy arrays."""
    assert Path(mat_file_path).exists(), f"File not found: {mat_file_path}"
    data = scipy.io.loadmat(mat_file_path)

    return data


def W_per_m2_to_W_per_room(u_radiators: np.ndarray) -> np.ndarray:
    """Convert radiator input from W/m2 to W per room using room areas."""
    assert u_radiators.shape[1] == 5, "Input dimension mismatch"
    room_areas = np.array(ROOM_AREAS)  # shape (5,)
    u_W_per_room = u_radiators * room_areas  # Broadcasting
    return u_W_per_room


def get_test_set_disturbances(
    brcm_mat_file: Path, datamodule: L.LightningDataModule
) -> pd.DataFrame:
    """Load disturbances for the test set (based on the datamodule configuration) from the BRCM .mat file and return as a pandas DataFrame indexed by timestamps."""
    test_indices = tuple(idx + 500 for idx in datamodule.test_indices)
    test_slice = slice(test_indices[0], test_indices[1])
    data = read_mat_file(brcm_mat_file)
    Tamb_seq = data["Tamb"]
    SolRad_seq = data["SolRad"]
    timestamps = data["time_posix"].astype("datetime64[s]").flatten()
    disturbances = np.hstack((Tamb_seq, SolRad_seq))
    df = pd.DataFrame(disturbances, columns=["Tamb", "SolRad"], index=timestamps)[
        test_slice
    ]
    assert df.isna().sum().sum() == 0, "NaN values found in disturbances dataframe"
    assert df.shape[0] == test_indices[1] - test_indices[0], (
        "Mismatch in number of validation disturbance samples"
    )
    assert df.shape[1] == 2, (
        "Disturbance dataframe should have 2 columns: Tamb and SolRad"
    )
    return df


class BRCMBuildingSimulator:
    def __init__(
        self,
        ss: BRCMStateSpaceModel | None = None,
        initial_temp: float = 20.0,
        dt_in_seconds: int = 30,
    ):
        if ss is None:
            ss = read_brcm_ss_mat_file(global_config.BRCM_MAT_FILE)
        self._initial_temp = initial_temp
        self.ss = ss
        self.x = np.ones((self.ss.nx,)) * initial_temp  # Initial state
        self.T_ground = 10.0  # Ground temperature (assumed constant)
        self.room_areas = global_config.ROOM_AREAS
        self.dt_in_seconds = dt_in_seconds

    @property
    def dt_in_hours(self) -> float:
        return self.dt_in_seconds / 3600.0

    @classmethod
    def from_mat_file(
        cls, mat_file_path: str | Path, initial_temp: float = 20.0
    ) -> "BRCMBuildingSimulator":
        ss = read_brcm_ss_mat_file(mat_file_path)
        return cls(ss, initial_temp)

    def reset(self, initial_temp: float | None = None) -> np.ndarray:
        if initial_temp is not None:
            self._initial_temp = initial_temp
        self.x = np.ones((self.ss.nx,)) * self._initial_temp
        return self.x

    def continuous_dynamics(self, x: np.ndarray, u: np.ndarray, d: np.ndarray):
        # Linear part
        dxdt = self.ss.A @ x + (self.ss.Bu @ u).ravel() + (self.ss.Bd @ d).ravel()

        # No Bilinear part for now
        return dxdt

    def simulate_one_step(
        self,
        u_radiators: np.ndarray,
        t_amb: float,
        solar_rad: float,
    ):
        """Simulate one time step by applying input u and disturbance d as piecewise constant over the time step of dt_sec.
        Args
        u: np.ndarray of shape (nu, 1)
            Control input in W/m2 for each room.
        d: np.ndarray of shape (nd, 1)
            Disturbance input in physical units (e.g., °C for ambient temperature, W/m2 for solar radiation).
        Returns
        x_next: np.ndarray of shape (nx,)
            Next state after applying input u and disturbance d for dt_sec.
        """
        assert u_radiators.shape == (5,), (
            f"Input dimension mismatch, u_radiators should be of shape (5,), got {u_radiators.shape}. Make sure to provide radiator inputs for 1 step, for all 5 rooms."
        )

        u_full = np.zeros(self.ss.Bu.shape[1])

        u_full[ControlIdx.RADIATOR1 :] = np.ravel(u_radiators)

        disturbances = np.zeros((self.ss.nd, 1))
        # first 5 disturbances are Internal Gains and are currently not used (assumed zero)
        disturbances[DisturbanceIdx.T_AMB] = t_amb
        disturbances[DisturbanceIdx.T_GROUND] = self.T_ground
        disturbances[DisturbanceIdx.SOLAR_EAST] = 0.5 * solar_rad
        disturbances[DisturbanceIdx.SOLAR_NORTH] = 0.5 * solar_rad
        disturbances[DisturbanceIdx.SOLAR_SOUTH] = solar_rad

        sol = scipy.integrate.solve_ivp(
            fun=lambda t, x: self.continuous_dynamics(x, u_full, disturbances),
            t_span=(0, self.dt_in_seconds),
            y0=self.x,
            method="RK45",
            atol=1e-6,
            rtol=1e-3,
        )

        self.x = sol.y[:, -1]  # Update state to last time point
        return self.x[:5]  # Return only the first 5 inputs (Room temperature states)

    def simulate_multi_step(
        self,
        u_radiators: np.ndarray,
        t_amb: np.ndarray,
        solar_rad: np.ndarray,
    ):
        """Simulate multiple steps by applying a sequence of inputs and disturbance as piecewise constant over each time step"""

        n_steps = u_radiators.shape[0]
        assert t_amb.shape == solar_rad.shape == (n_steps,), "Input dimension mismatch"

        room_temps_traj = np.zeros((n_steps + 1, 5))
        room_temps_traj[0, :] = self.x[:5]

        for k in range(n_steps):
            room_temps = self.simulate_one_step(
                u_radiators=u_radiators[k, :],
                t_amb=t_amb[k].item(),
                solar_rad=solar_rad[k].item(),
            )
            room_temps_traj[k + 1, :] = room_temps

        return room_temps_traj
