from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING

from alphabuilding.domain.types import (
    GraphTopology,
)


@dataclass
class OptimizerConfig:
    _target_: str = MISSING
    _partial_: bool = True
    lr: float = MISSING
    weight_decay: float = 0.0


@dataclass
class A_moduleConfig:
    _target_: str = MISSING
    _partial_: bool = True


@dataclass
class DynamicsConfig:
    _recursive_: bool = False
    num_inputs: int = 5
    num_disturbances: int = 2
    B_initializer: str = "physical"
    B_scale: float = 0.01
    scale: float = 0.01
    A_module: A_moduleConfig = field(default_factory=A_moduleConfig)


@dataclass
class DiscreteObserverODEConfig:
    _target_: str = (
        "alphabuilding.infrastructure.lightning.modules.discrete_observer_ode."
        "LitMultiStepNeuralDiscreteODEModule"
    )

    dynamics: DynamicsConfig = field(default_factory=DynamicsConfig)

    optimizer: OptimizerConfig = MISSING
    lr_scheduler: Any = None

    horizon: int = MISSING
    window_size: int = MISSING
    num_latent_states: int = 0
    lr: float = 1e-2
    weight_decay: float = 0.0
    topology: GraphTopology = GraphTopology.PHYSICAL_ONE_TO_ONE
    lambda_eigenvals_stability_penalty: float = 0.0
    lambda_observer: float = 0.3


@dataclass
class DataModuleConfig:
    _target_: str = MISSING
    csv_file: Path = MISSING
    batch_size: int = MISSING
    num_workers: int = 0
    size: int | None = None
    window_size: int = MISSING
    initial_horizon: int = MISSING
    max_horizon: int = MISSING
    train_ratio: float = MISSING
    val_ratio: float = MISSING
    noise_stds: list[float] = MISSING

    def __post_init__(self):
        if len(self.noise_stds) != 2:
            raise ValueError(
                f"noise_stds must be a list of exactly 2 floats, "
                f"got {len(self.noise_stds)}"
            )
        for std in self.noise_stds:
            if std < 0:
                raise ValueError(
                    f"Noise standard deviations must be non-negative, got {std}"
                )


cs = ConfigStore.instance()
cs.store(group="model", name="default_schema", node=DiscreteObserverODEConfig)
cs.store(group="optimizer", name="adamw", node=OptimizerConfig)
cs.store(group="dynamics", name="soft_stable_metzler_dynamics", node=DynamicsConfig)
cs.store(group="datamodule", name="default_schema", node=DataModuleConfig)
