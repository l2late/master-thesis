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
skip_steps = 0

# Define all your plot configurations
base_dir = (
    paths.log_dir
    / "vastai"
    / "linear_ph_observer_midterm"
    / "multiruns"
    / "2025-12-02_09-44-02"
)


exp1 = "experiment=15_minutes_real_random_lph_observer_rc_cosine,model.lambda_frequency_loss=0,model.num_mass_states_per_zone=0,trainer.max_epochs=2000"
exp2 = "experiment=15_minutes_real_random_lph_observer_rc_cosine,model.lambda_frequency_loss=0,model.num_mass_states_per_zone=1,trainer.max_epochs=2000"
exp3 = "experiment=15_minutes_real_random_lph_observer_rc_cosine,model.lambda_frequency_loss=0,model.num_mass_states_per_zone=2,trainer.max_epochs=2000"

log_dirs = [
    base_dir / exp1,
    base_dir / exp2,
    base_dir / exp3,
]

plot_configs = [
    # effect of hidden states on training loss for B positivity constraint
    PlotConfig(
        log_dirs=log_dirs,
        labels=["0 Latent states", "5 Latent states", "10 Latent states"],
        metric="train/trace_mse",
        title="Training Loss",
        ylabel="MSE",
        smoothing=default_smooting,
        use_log_scale=True,
        skip_steps=skip_steps,
        save_filename="midterm_train_mse",
        save_format=default_save_format,
    ),
    # Validation loss RMSE
    PlotConfig(
        log_dirs=log_dirs,
        labels=["0 Latent states", "5 Latent states", "10 Latent states"],
        metric="val/rmse_celsius",
        title="Validation Loss",
        ylabel="RMSE (°C)",
        smoothing=default_smooting,
        use_log_scale=True,
        skip_steps=skip_steps,
        save_filename="midterm_val_rmse",
        save_format=default_save_format,
    ),
    # Validation loss RMSE
    PlotConfig(
        log_dirs=log_dirs,
        labels=["0 Latent states", "5 Latent states", "10 Latent states"],
        metric="val/max_abs_error_celsius",
        title="Validation Max Absolute Error (°C)",
        ylabel="Max Absolute Error (°C)",
        smoothing=default_smooting,
        use_log_scale=False,
        skip_steps=skip_steps,
        save_filename="midterm_val_max_abs_error",
        save_format=default_save_format,
    ),
]
