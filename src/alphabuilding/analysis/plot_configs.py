from dataclasses import dataclass
from pathlib import Path

from alphabuilding.utils.paths import paths


@dataclass
class PlotConfig:
    """Configuration for a single plot."""

    log_dirs: list[str | Path]
    labels: list[str]
    metric: str
    skip_steps: int = 0

    title: str | None = None
    ylabel: str | None = None
    smoothing: float = 0.0
    use_log_scale: bool = False

    save_filename: str | None = None
    save_format: str = "png"  # "png", "pdf", or "svg"

    def __post_init__(self):
        """Convert string paths to Path objects."""
        self.log_dirs = [Path(d) if isinstance(d, str) else d for d in self.log_dirs]

        # Validate
        if len(self.log_dirs) != len(self.labels):
            raise ValueError(
                f"Number of log_dirs ({len(self.log_dirs)}) must match labels ({len(self.labels)})"
            )


default_smooting = 0.99
default_save_format = "png"

# Define all your plot configurations
plot_configs = [
    # effect of hidden states on training loss for B positivity constraint
    PlotConfig(
        log_dirs=[
            paths.log_dir
            / "selected/linear_full_B_pos/2025-11-07_11-31-23/datamodule.batch_size=512,datamodule.val_ratio=0.5,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=0,trainer.max_epochs=10000",
            paths.log_dir
            / "selected/linear_full_B_pos/2025-11-07_11-31-23/datamodule.batch_size=512,datamodule.val_ratio=0.5,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=5,trainer.max_epochs=10000",
            paths.log_dir
            / "selected/linear_full_B_pos/2025-11-07_11-31-23/datamodule.batch_size=512,datamodule.val_ratio=0.5,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=10,trainer.max_epochs=10000",
        ],
        labels=["0 Hidden States", "5 Hidden States", "10 Hidden States"],
        metric="train/trace_mse",
        title="Training Loss",
        ylabel="Trace MSE",
        smoothing=default_smooting,
        use_log_scale=True,
        skip_steps=500,
        save_filename="train_loss_10000_epochs_B_pos",
        save_format=default_save_format,
    ),
    # Validation loss
    PlotConfig(
        log_dirs=[
            paths.log_dir
            / "selected/linear_full_B_pos/2025-11-07_11-31-23/datamodule.batch_size=512,datamodule.val_ratio=0.5,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=0,trainer.max_epochs=10000",
            paths.log_dir
            / "selected/linear_full_B_pos/2025-11-07_11-31-23/datamodule.batch_size=512,datamodule.val_ratio=0.5,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=5,trainer.max_epochs=10000",
            paths.log_dir
            / "selected/linear_full_B_pos/2025-11-07_11-31-23/datamodule.batch_size=512,datamodule.val_ratio=0.5,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=10,trainer.max_epochs=10000",
        ],
        labels=["0 Hidden States", "5 Hidden States", "10 Hidden States"],
        metric="val/trace_mse",
        title="Validation Loss",
        ylabel="Trace MSE",
        smoothing=default_smooting,
        use_log_scale=True,
        skip_steps=500,
        save_filename="val_loss_10000_epochs_B_pos",
        save_format=default_save_format,
    ),
    # no positivity constraint
    PlotConfig(
        log_dirs=[
            paths.log_dir
            / "selected/linear_full_B_unconstrained"
            / "datamodule.batch_size=512,datamodule.val_ratio=0.1,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=0,trainer.max_epochs=10000",
            paths.log_dir
            / "selected/linear_full_B_unconstrained"
            / "datamodule.batch_size=512,datamodule.val_ratio=0.1,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=5,trainer.max_epochs=10000",
        ],
        labels=["0 Hidden States", "5 Hidden States"],
        metric="val/trace_mse",
        title="Validation Loss",
        ylabel="Trace MSE",
        smoothing=default_smooting,
        use_log_scale=True,
        save_filename="val_loss_no_B_constraint",
        save_format=default_save_format,
    ),
    PlotConfig(
        log_dirs=[
            paths.log_dir
            / "selected/linear_full_B_unconstrained"
            / "datamodule.batch_size=512,datamodule.val_ratio=0.1,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=0,trainer.max_epochs=10000",
            paths.log_dir
            / "selected/linear_full_B_unconstrained"
            / "datamodule.batch_size=512,datamodule.val_ratio=0.1,experiment=15_minutes_real_hysteresis_linear_full_cosine_small_sets_B_pos,model.num_mass_states_per_zone=5,trainer.max_epochs=10000",
        ],
        labels=["0 Hidden States", "5 Hidden States"],
        metric="train/trace_mse",
        title="Training Loss",
        ylabel="Trace MSE",
        smoothing=default_smooting,
        use_log_scale=True,
        save_filename="train_loss_no_B_constraint",
        save_format=default_save_format,
    ),
]
