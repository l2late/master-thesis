import math

import numpy as np

from alphabuilding.control.lti_analysis import (
    compute_continuous_tau_max,
    compute_discrete_tau_max,
    compute_settling_time,
)


def test_compute_tau_max_continuous_stable():
    lambda_1 = -0.5
    lambda_2 = -1
    A = np.array([[lambda_1, 0], [0, lambda_2]])
    tau_max = compute_continuous_tau_max(A)
    expected_tau_max = -1 / lambda_1
    assert abs(tau_max - expected_tau_max) < 1e-6, (
        f"Expected tau_max to be {expected_tau_max}, but got {tau_max}"
    )


def test_compute_tau_max_continuous_unstable():
    lambda_1 = 0.5
    lambda_2 = -1
    A = np.array([[lambda_1, 0], [0, lambda_2]])
    tau_max = compute_continuous_tau_max(A)
    assert tau_max == 0.0, (
        f"Expected tau_max to be 0.0 for unstable system, but got {tau_max}"
    )


def test_compute_tau_max_discrete_stable():
    lambda_1 = 0.8
    lambda_2 = 0.5
    dt = 0.1
    A = np.array([[lambda_1, 0], [0, lambda_2]])
    tau_max = compute_discrete_tau_max(A, dt=dt)
    expected_tau_max = -dt / np.log(lambda_1)
    assert abs(tau_max - expected_tau_max) < 1e-6, (
        f"Expected tau_max to be {expected_tau_max}, but got {tau_max}"
    )


def test_compute_tau_max_discrete_unstable():
    lambda_1 = 1.0001
    lambda_2 = 0.5
    A = np.array([[lambda_1, 0], [0, lambda_2]])
    tau_max = compute_discrete_tau_max(A, dt=0.1)
    assert tau_max == 0.0, (
        f"Expected tau_max to be 0.0 for unstable system, but got {tau_max}"
    )


def test_compute_settling_time_for_continuous_sys():
    lambda_1 = -0.5
    lambda_2 = -1
    tau_max = -1 / lambda_1

    tol = 2
    tol_fraction = tol / 100  # Convert percentage to fraction

    t_expected = -math.log(tol_fraction) * tau_max

    A = np.array([[lambda_1, 0], [0, lambda_2]])
    t = compute_settling_time(A, tol=2)
    assert abs(t - t_expected) < 1e-6, (
        f"Expected settling time to be {t_expected}, but got {t}"
    )


def test_compute_settling_time_for_discrete_sys():
    lambda_1 = 0.5
    lambda_2 = 0.9  # <- dominant pole is the one closest to unit circle

    tol = 2
    tol_percent = tol / 100

    dt = 0.1

    k_expected = math.log(tol_percent) / math.log(lambda_2)
    t_expected = math.ceil(k_expected) * dt  # Round up to the nearest time step

    A = np.array([[lambda_1, 0], [0, lambda_2]])
    t_computed = compute_settling_time(A, dt=dt, tol=2)
    assert abs(t_computed - t_expected) < 1e-6, (
        f"Expected settling time to be {t_expected}, but got {t_computed}"
    )
