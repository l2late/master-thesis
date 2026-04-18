from alphabuilding.application.factories import DomainDatasetFactory
from conf.config import FIVE_ROOM_BRCM_SIMULATION_RESULTS_CSV
from alphabuilding.domain.entities import PhysicalQuantity
from alphabuilding.infrastructure.data_access.file_data_readers import CsvDataReader


def init_matlab_dataset():
    COLUMN_MAP = {
        "ZoneMeanAirTemperature 2": PhysicalQuantity("Temperature", "Celsius"),
        "ZoneMeanAirTemperature 1": PhysicalQuantity("Temperature", "Celsius"),
        "ZoneMeanAirTemperature 3": PhysicalQuantity("Temperature", "Celsius"),
        "ZoneMeanAirTemperature 4": PhysicalQuantity("Temperature", "Celsius"),
        "ZoneMeanAirTemperature 5": PhysicalQuantity("Temperature", "Celsius"),
        "Environment": PhysicalQuantity("Temperature", "Celsius"),
        "HeatInput 1": PhysicalQuantity("Heat Input", "Watt"),
        "HeatInput 2": PhysicalQuantity("Heat Input", "Watt"),
        "HeatInput 3": PhysicalQuantity("Heat Input", "Watt"),
        "HeatInput 4": PhysicalQuantity("Heat Input", "Watt"),
        "HeatInput 5": PhysicalQuantity("Heat Input", "Watt"),
    }

    # SCALING_STRATEGY = {
    #     PhysicalQuantity("Temperature", "Celsius"): SklearnMinMaxScaler,
    #     PhysicalQuantity("Heat Input", "Watt"): SklearnMinMaxScaler,
    # }

    DATA_FILE = FIVE_ROOM_BRCM_SIMULATION_RESULTS_CSV

    dataset_factory = DomainDatasetFactory()
    dataset_reader = CsvDataReader()
    dataset_loader = PandasCsvDatasetLoader(dataset_reader, dataset_factory)

    dataset = dataset_loader.load(
        file_path=DATA_FILE,
        timestamp_col="Datetime",
        column_to_quantity_map=COLUMN_MAP,
        skiprows=1000,
    )
    print(f"Loaded dataset with {len(dataset)} time series.\n")

    return dataset
