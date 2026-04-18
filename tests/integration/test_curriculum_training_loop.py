import lightning as L
import pytest

import conf.config as config
from domain.errors import (
    DataModuleMaxHorizonLessThanModuleHorizonError,
    HorizonsNotEqualError,
)
from infrastructure.lightning.callbacks.curriculum_callbacks import (
    CurriculumOnMetricPlateauCallback,
    CurriculumOnScheduleCallback,
)
from infrastructure.lightning.datamodules.brcm_datamodule import (
    BRCMTrajectoryLitDataModule,
)

PAST_WINDOW = 2
MAX_HORIZON = 4
INITIAL_HORIZON = 1
NUM_ZONE_TEMPS = 5
NUM_HEAT_INPUTS = 5


def make_trainer_with_horizon_scheduler_callback(
    max_epochs: int = 1,
    gradient_clip_val=config.GRADIENT_CLIP_VAL,
    check_val_every_n_epoch=2,
    # check_val_every_n_epoch=1,
    num_sanity_val_steps=0,
    reload_dataloaders_every_n_epochs=1,
    horizon_schedule: dict[int, int] | None = None,
):
    if horizon_schedule is None:
        horizon_schedule = {
            0: INITIAL_HORIZON,
            1: INITIAL_HORIZON + 1,
            2: INITIAL_HORIZON + 2,
        }
    else:
        horizon_schedule = horizon_schedule

    max_epochs = max(max_epochs, max(horizon_schedule.keys()) + 1)
    callbacks = [CurriculumOnScheduleCallback(horizon_schedule=horizon_schedule)]

    return L.Trainer(
        accelerator=config.ACCELERATOR,
        max_epochs=max_epochs,
        gradient_clip_val=gradient_clip_val,
        check_val_every_n_epoch=check_val_every_n_epoch,
        reload_dataloaders_every_n_epochs=reload_dataloaders_every_n_epochs,
        num_sanity_val_steps=num_sanity_val_steps,
        callbacks=callbacks,
        limit_train_batches=1,
        limit_val_batches=1,
    )


def make_trainer_with_horizon_on_plateau_callback(
    max_epochs: int = 1,
    gradient_clip_val=config.GRADIENT_CLIP_VAL,
    check_val_every_n_epoch=2,
    num_sanity_val_steps=0,
    reload_dataloaders_every_n_epochs=1,
):
    callbacks = [CurriculumOnMetricPlateauCallback(metric="val/loss", patience=1)]

    return L.Trainer(
        accelerator=config.ACCELERATOR,
        max_epochs=max_epochs,
        gradient_clip_val=gradient_clip_val,
        check_val_every_n_epoch=check_val_every_n_epoch,
        reload_dataloaders_every_n_epochs=reload_dataloaders_every_n_epochs,
        num_sanity_val_steps=num_sanity_val_steps,
        callbacks=callbacks,
        limit_train_batches=1,
        limit_val_batches=1,
    )


# def test_fit_loop_with_unequal_horizons_fails(five_room_csv):
#     trainer = make_trainer_with_horizon_scheduler_callback()
#     batch_size = 2
#
#     dm = BRCMTrajectoryLitDataModule(
#         csv_file=five_room_csv,
#         batch_size=batch_size,
#         size=30,
#         window_size=PAST_WINDOW,
#         max_horizon=MAX_HORIZON,
#         initial_horizon=INITIAL_HORIZON,
#     )
#     model = make_model(horizon=INITIAL_HORIZON + 1)
#
#     with pytest.raises(HorizonsNotEqualError):
#         trainer.fit(
#             model=model,
#             datamodule=dm,
#         )
#
#
# def test_fit_loop_with_datamodule_max_horizon_less_than_module_horizon_fails(
#     five_room_csv,
# ):
#     trainer = make_trainer_with_horizon_scheduler_callback()
#     batch_size = 2
#
#     dm = BRCMTrajectoryLitDataModule(
#         csv_file=five_room_csv,
#         batch_size=batch_size,
#         size=30,
#         window_size=PAST_WINDOW,
#         max_horizon=MAX_HORIZON,
#     )
#     model = make_model(
#         horizon=MAX_HORIZON + 1
#     )  # Intentionally set horizon larger than initial horizon
#
#     with pytest.raises(DataModuleMaxHorizonLessThanModuleHorizonError):
#         trainer.fit(model=model, datamodule=dm)


# TODO: because i now have conditional logic in the model init, it might not create a GRU history encoder.
# I guess thats why it fails now.
# @pytest.mark.slow
# def test_fit_loop_with_valid_horizon_settings(five_room_csv):
#     trainer = make_trainer_with_horizon_scheduler_callback()
#     batch_size = 2
#
#     dm = BRCMTrajectoryLitDataModule(
#         csv_file=five_room_csv,
#         batch_size=batch_size,
#         size=40,
#         window_size=PAST_WINDOW,
#         max_horizon=MAX_HORIZON,
#         initial_horizon=INITIAL_HORIZON,
#     )
#     model = make_model(
#         horizon=INITIAL_HORIZON,
#     )
#     trainer.fit(model=model, datamodule=dm)
#     assert model.horizon > INITIAL_HORIZON
#     assert dm.current_horizon > INITIAL_HORIZON


# @pytest.mark.slow
# def test_fit_loop_with_horizon_curriculum_schedule(five_room_csv):
#     horizon_schedule = {
#         0: 1,
#         1: 2,
#         2: 3,
#         3: 4,
#     }
#     trainer = make_trainer_with_horizon_scheduler_callback(
#         max_epochs=6, horizon_schedule=horizon_schedule
#     )
#     batch_size = 10
#
#     dm = BRCMTrajectoryLitDataModule(
#         csv_file=five_room_csv,
#         batch_size=batch_size,
#         size=50,
#         window_size=PAST_WINDOW,
#         max_horizon=4,
#         initial_horizon=INITIAL_HORIZON,
#     )
#     model = make_model(
#         horizon=INITIAL_HORIZON,
#     )
#
#     trainer.fit(model=model, datamodule=dm)


# @pytest.mark.slow
# def test_fit_loop_with_curriculum_change_on_metric_plateau(five_room_csv):
#     trainer = make_trainer_with_horizon_on_plateau_callback(max_epochs=25)
#     batch_size = 2
#
#     dm = BRCMTrajectoryLitDataModule(
#         csv_file=five_room_csv,
#         batch_size=batch_size,
#         size=100,
#         window_size=PAST_WINDOW,
#         max_horizon=4,
#         initial_horizon=INITIAL_HORIZON,
#     )
#     model = make_model(
#         horizon=INITIAL_HORIZON,
#     )
#
#     trainer.fit(model=model, datamodule=dm)
#     print("Final horizon:", model.horizon)
#     print("Final current horizon:", dm.current_horizon)
#     assert dm.current_horizon > INITIAL_HORIZON
#     assert model.horizon > INITIAL_HORIZON
