import io
from pathlib import Path

# import pandas as pd
import pytest

from alphabuilding.control.brcm_building import (
    test_disturbances,
)
from alphabuilding.control.utils import (
    load_learned_lti_ss,
)
from alphabuilding.domain.types import Scalers
from alphabuilding.utils.paths import paths

# from domain.entities import PhysicalQuantity, Dataset
# from infrastructure.data_access.file_data_readers import CsvDataReader
# from application.services.brcm_dataset_creation_service import BRCMDatasetCreationService


@pytest.fixture
def in_memory_five_room_csv() -> io.StringIO:
    """
    Creates an in-memory csv.
    """
    csv_data = """Datetime,ZoneMeanAirTemperature 1,ZoneMeanAirTemperature 2,ZoneMeanAirTemperature 3,ZoneMeanAirTemperature 4,ZoneMeanAirTemperature 5,Environment,HeatInput 1,HeatInput 2,HeatInput 3,HeatInput 4,HeatInput 5
    01-Jan-2008 00:00:00,19,19,19,19,19,-10,0,0,4200,6600,0
    01-Jan-2008 01:00:00,14.968012207672,14.968012207672,20.0511833576426,18.5879218470329,14.4625223953623,20,0,0,0,0,0
    01-Jan-2008 02:00:00,18.9337920234729,18.9337920234729,19.026747613089,19.0963428479774,18.9430910772492,20,4200,4200,4200,0,1800
    01-Jan-2008 03:00:00,22.2859730945724,22.2859730945724,21.5537271719687,19.1085135306486,21.8513117255101,-10,0,4200,4200,0,0
    01-Jan-2008 04:00:00,14.9863159842433,18.2866795331393,20.1866752379094,15.1247471686232,14.4226287123531,-10,0,0,4200,6600,0
    01-Jan-2008 05:00:00,14.7555070536348,14.8931977765654,20.1277017270089,18.3710530168695,14.1704995211891,20,4200,4200,0,0,1800
    01-Jan-2008 06:00:00,22.0478112612363,22.1565303860605,19.0962259027445,18.897627603976,21.535923391252,-10,4200,0,4200,0,1800
    01-Jan-2008 07:00:00,18.0549057992272,14.8576168346934,20.0902941206925,14.8980249260096,16.9863224130585,-10,0,4200,4200,6600,1800
    01-Jan-2008 08:00:00,14.659746016437,17.9209071416909,20.0522883496426,18.1425450262499,16.8591462570379,20,4200,0,4200,6600,1800
    01-Jan-2008 09:00:00,21.9288201040805,18.751657270417,21.5477077701512,22.1277883323426,21.4832523129943,20,0,4200,0,0,1800
    """

    # Use io.StringIO to treat the string as a file
    return io.StringIO(csv_data)


@pytest.fixture(scope="module")
def five_room_csv() -> Path:
    """
    Returns the path to the BRCM five room CSV file.
    """
    return Path(
        "tests/data/matlab_brcm_simulation_results/five_room_building_simulation_results.csv"
    )


@pytest.fixture
def adam_optimizer():
    import torch.optim as optim

    return optim.Adam


@pytest.fixture
def lr_scheduler():
    import torch.optim.lr_scheduler as lr_scheduler

    return lr_scheduler.ReduceLROnPlateau


@pytest.fixture(scope="session")
def mat_file_path():
    return paths.data_dir / "building_plant_data.mat"


@pytest.fixture(scope="session")
def internal_model():
    ss_model, _, _, _ = load_learned_lti_ss()
    return ss_model


@pytest.fixture(scope="session")
def datamodule():
    _, datamodule, _, _ = load_learned_lti_ss()
    return datamodule


@pytest.fixture(scope="session")
def validation_disturbances_df(mat_file_path, datamodule):
    return test_disturbances(mat_file_path, datamodule)


@pytest.fixture(scope="session")
def controller_input_df(validation_disturbances_df):
    df = validation_disturbances_df
    df["Tmin"] = np.ones(df.shape[0]) * 18.0
    df["Tmax"] = np.ones(df.shape[0]) * 24.0
    ControllerInput.validate(df)
    return df


@pytest.fixture(scope="session")
def scalers(datamodule):
    scalers = Scalers(
        temp=datamodule.zone_temp_scaler,
        amb=datamodule.ambient_temp_scaler,
        sol=datamodule.solar_radiation_scaler,
        heat=datamodule.heat_input_scaler,
    )
    return scalers


#
#
# @pytest.fixture
# def in_memory_five_room_df(in_memory_five_room_csv) -> pd.DataFrame:
#     """
#     Creates a complex DataFrame from an in-memory text block.
#     """
#     index = "Datetime"
#     return pd.read_csv(
#         in_memory_five_room_csv,
#         index_col=index,
#         parse_dates=[index],
#     )
#
#
# @pytest.fixture
# def five_room_df_col_to_quantity_map() -> dict[str, PhysicalQuantity]:
#     """
#     Creates a complex DataFrame from an in-memory text block.
#     """
#     col_to_qty_map = {
#         "ZoneMeanAirTemperature 2": PhysicalQuantity("Temperature", "Celsius"),
#         "ZoneMeanAirTemperature 1": PhysicalQuantity("Temperature", "Celsius"),
#         "ZoneMeanAirTemperature 3": PhysicalQuantity("Temperature", "Celsius"),
#         "ZoneMeanAirTemperature 4": PhysicalQuantity("Temperature", "Celsius"),
#         "ZoneMeanAirTemperature 5": PhysicalQuantity("Temperature", "Celsius"),
#         "Environment": PhysicalQuantity("Temperature", "Celsius"),
#         "HeatInput 1": PhysicalQuantity("Heat Input", "Watt"),
#         "HeatInput 2": PhysicalQuantity("Heat Input", "Watt"),
#         "HeatInput 3": PhysicalQuantity("Heat Input", "Watt"),
#         "HeatInput 4": PhysicalQuantity("Heat Input", "Watt"),
#         "HeatInput 5": PhysicalQuantity("Heat Input", "Watt"),
#     }
#     return col_to_qty_map
#
#
# @pytest.fixture
# def in_memory_dataset() -> Dataset
