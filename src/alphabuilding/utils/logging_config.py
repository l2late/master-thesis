import logging
from pathlib import Path

from alphabuilding.utils.paths import paths

FMT = "%(asctime)s [sim=%(sim_time)s] %(name)s %(levelname)s | %(message)s"


class SimTimeFilter(logging.Filter):
    """Injects current sim_time into every log record passing through."""

    def __init__(self):
        super().__init__()
        self.sim_time: str = "-"

    def filter(self, record: logging.LogRecord) -> bool:
        record.sim_time = self.sim_time
        return True


# module-level singleton — import this wherever you need to update sim_time
sim_time_filter = SimTimeFilter()


def setup_logging(log_file: str | None = None, level=logging.DEBUG):
    if log_file is None:
        log_file = Path(paths.log_dir) / "mpc_debug.log"
    # Add sim_time default so records from loggers WITHOUT the adapter don't crash
    old_factory = logging.getLogRecordFactory()

    def factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        if not hasattr(record, "sim_time"):
            record.sim_time = "-"
        return record

    logging.setLogRecordFactory(factory)
    handler_file = logging.FileHandler(log_file, mode="w")
    handler_console = logging.StreamHandler()

    for h in (handler_file, handler_console):
        h.setFormatter(logging.Formatter(FMT))
        h.addFilter(sim_time_filter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler_file)
    root.addHandler(handler_console)
