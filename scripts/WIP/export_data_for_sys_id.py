import hydra
from hydra.utils import instantiate
from lightning import LightningDataModule
from omegaconf import DictConfig

from alphabuilding.application.use_cases.export_data_for_sys_id import (
    export_datamodule_to_matlab,
)
from alphabuilding.infrastructure.lightning.datamodules.brcm_datamodule import (
    BRCMTrajectoryLitDataModule,
)
from alphabuilding.utils.paths import PathsConfig, paths


@hydra.main(version_base="1.3", config_path="../../conf", config_name="train")
def main(cfg: DictConfig) -> None:
    output_path = paths.data_dir / "system_id_data.mat"
    datamodule = BRCMTrajectoryLitDataModule(
        csv_file=cfg.datamodule.csv_file, batch_size=cfg.datamodule.batch_size
    )
    datamodule: LightningDataModule = instantiate(cfg.datamodule)
    assert isinstance(datamodule, BRCMTrajectoryLitDataModule), (
        "Expected a BRCMTrajectoryLitDataModule instance"
    )
    export_datamodule_to_matlab(datamodule, output_path=output_path)


if __name__ == "__main__":
    main()
