import math

import lightning as L


class CosineAnnealingHparam(L.Callback):
    """Schedules a LightningModule attribute using cosine annealing.

    The value follows the cosine decay formula:

        value(t) = end + 0.5 * (start - end) * (1 + cos(pi * t / T_max))

    which smoothly interpolates from `start` at epoch 0 to `end` at epoch
    `T_max`, then stays at `end` for any subsequent epochs. The scheduled
    value is also logged to the trainer's logger under `attr`.

    Args:
        attr:   Name of the attribute on the LightningModule to schedule.
        start:  Value at the beginning of training (epoch 0).
        end:    Value at the end of the annealing period (epoch T_max).
        T_max:  Number of epochs over which the annealing takes place.

    Example::

        callback = CosineAnnealingHparam("kl_weight", start=0.0, end=1.0, T_max=50)
        trainer = L.Trainer(max_epochs=100, callbacks=[callback])
    """

    def __init__(self, attr: str, start: float, end: float, T_max: int):
        super().__init__()
        self.attr = attr
        self.start = start
        self.end = end
        self.T_max = T_max

    def on_train_epoch_start(
        self, trainer: L.Trainer, pl_module: L.LightningModule
    ) -> None:
        """Compute and apply the cosine-annealed value at the start of each epoch."""
        t = min(trainer.current_epoch, self.T_max)
        value = self.end + 0.5 * (self.start - self.end) * (
            1 + math.cos(math.pi * t / self.T_max)
        )
        setattr(pl_module, self.attr, value)
        pl_module.log(self.attr, value)


class ExponentialHparam(L.Callback):
    """Schedules a LightningModule attribute using exponential decay.

    The value follows:

        value(t) = start * gamma^t,   where gamma = (end / start)^(1 / T_max)

    This decays (or grows) multiplicatively each epoch so that `start` is the
    value at epoch 0 and `end` is reached exactly at epoch `T_max`. After
    `T_max`, the schedule continues to extrapolate geometrically. The scheduled
    value is logged to the trainer's logger under `attr`.

    Args:
        attr:   Name of the attribute on the LightningModule to schedule.
        start:  Value at epoch 0. Must be strictly positive (non-zero).
        end:    Target value at epoch T_max. Must be strictly positive (non-zero).
        T_max:  Number of epochs to reach `end` from `start`.

    Example::

        callback = ExponentialHparam("temperature", start=1.0, end=0.1, T_max=100)
        trainer = L.Trainer(max_epochs=100, callbacks=[callback])
    """

    def __init__(self, attr: str, start: float, end: float, T_max: int):
        super().__init__()
        if start == 0 or end == 0:
            raise ValueError(
                "`start` and `end` must be non-zero for exponential scheduling."
            )
        self.attr = attr
        self.start = start
        self.end = end
        self.T_max = T_max
        self.gamma = (end / start) ** (1.0 / T_max)

    def on_train_epoch_start(
        self, trainer: L.Trainer, pl_module: L.LightningModule
    ) -> None:
        """Compute and apply the exponentially decayed value at the start of each epoch."""
        value = self.start * (self.gamma**trainer.current_epoch)
        setattr(pl_module, self.attr, value)
        pl_module.log(self.attr, value)
