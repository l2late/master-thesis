import pandas as pd
import pandera as pa
import pytest

from src.domain.df_schemas import ControllerInput, SimulationResult


@pytest.fixture()
def valid_controller_input_df():
    data = {
        "datetime": pd.date_range(start="2024-01-01", periods=5, freq="15min"),
        "Tamb": [20.0, 21.5, 19.8, 22.1, 20.5],
        "SolRad": [300.0, 320.0, 310.0, 330.0, 305.0],
        "Tmin": [18.0, 18.0, 18.0, 18.0, 18.0],
        "Tmax": [24.0, 24.0, 24.0, 24.0, 24.0],
    }
    df = pd.DataFrame(data)
    df.set_index("datetime", inplace=True)
    return df


@pytest.fixture()
def valid_simulation_result_df():
    data = {
        "datetime": pd.date_range(start="2024-01-01", periods=5, freq="30s"),
        "Tamb": [20.0, 21.5, 19.8, 22.1, 20.5],
        "SolRad": [300.0, 320.0, 310.0, 330.0, 305.0],
        "Tmin": [18.0, 18.0, 18.0, 18.0, 18.0],
        "Tmax": [24.0, 24.0, 24.0, 24.0, 24.0],
        "u1": [0.1, 0.2, 0.15, 0.25, 0.1],
        "u2": [0.2, 0.3, 0.25, 0.35, 0.2],
        "u3": [0.3, 0.4, 0.35, 0.45, 0.3],
        "u4": [0.4, 0.5, 0.45, 0.55, 0.4],
        "u5": [0.5, 0.6, 0.55, 0.65, 0.5],
        "y1": [22.0, 22.5, 21.8, 23.1, 22.5],
        "y2": [23.0, 23.5, 22.8, 24.1, 23.5],
        "y3": [24.0, 24.5, 23.8, 25.1, 24.5],
        "y4": [25.0, 25.5, 24.8, 26.1, 25.5],
        "y5": [26.0, 26.5, 25.8, 27.1, 26.5],
    }
    df = pd.DataFrame(data)
    df.set_index("datetime", inplace=True)
    return df


def test_valid_controller_input(valid_controller_input_df):
    ControllerInput.validate(valid_controller_input_df)


def test_invalid_controller_input_raises_error(valid_controller_input_df):
    # drop one column
    invalid_df = valid_controller_input_df.drop(columns=["Tamb"])
    with pytest.raises(pa.errors.SchemaError):
        ControllerInput.validate(invalid_df)


def test_invalid_index_freq_controller_input_raises_error(valid_controller_input_df):
    # drop one column

    invalid_df = valid_controller_input_df.index
    # replace index with wrong frequency
    invalid_df = valid_controller_input_df.copy()
    invalid_df.index = pd.date_range(start="2024-01-01", periods=5, freq="10min")
    with pytest.raises(pa.errors.SchemaError):
        ControllerInput.validate(invalid_df)


def test_valid_simulation_result(valid_simulation_result_df):
    SimulationResult.validate(valid_simulation_result_df)


def test_invalid_simulation_result_raises_error(valid_simulation_result_df):
    # drop one column
    invalid_df = valid_simulation_result_df.drop(columns=["u1"])
    with pytest.raises(pa.errors.SchemaError):
        SimulationResult.validate(invalid_df)


def test_invalid_index_freq_simulation_result_raises_error(valid_simulation_result_df):
    # drop one column
    invalid_df = valid_simulation_result_df.index
    # replace index with wrong frequency
    invalid_df = valid_simulation_result_df.copy()
    invalid_df.index = pd.date_range(start="2024-01-01", periods=5, freq="1min")
    with pytest.raises(pa.errors.SchemaError):
        SimulationResult.validate(invalid_df)
