from pathlib import Path

import numpy as np
import scipy.io

from alphabuilding.control.types import TimedStateSpace


# NOTE: WIP - need to import the N4SID model from MATLAB and convert it to a format that we can use in Python.
# The N4SID model includes the state-space matrices (A, B, C, D) and the observer gain K.
# We also need to ensure that the sample time (Ts) is correctly handled when creating the TimedStateSpace object.
# Then use this in the MPC BO hyper parameter optimization to compare the performance of the N4SID model with the neural state-space models that we trained.
def load_matlab_n4sid_model(path: Path) -> tuple[TimedStateSpace, np.ndarray]:
    ssopt_model = scipy.io.loadmat(path)
    dt = ssopt_model["Ts"].item() * 60  # Convert from minutes to seconds
    A = ssopt_model["A"]
    B = ssopt_model["B"]
    C = ssopt_model["C"]
    D = ssopt_model["D"]

    print("A matrix shape:", A.shape)
    print("B matrix shape:", B.shape)
    print("C matrix shape:", C.shape)
    assert np.sum(D) == 0, "Expected D matrix to be zero"

    system = scipy.signal.StateSpace(
        A,
        B,
        C,
        D,
        dt=dt,
    )
    time_unit = "seconds"  # matlab returns the 15 minutes
    K = ssopt_model["K"]
    sys_learned = TimedStateSpace(system, dt, time_unit)
    return sys_learned, K
