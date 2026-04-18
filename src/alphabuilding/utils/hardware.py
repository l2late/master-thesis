import math
import os


def _cpu_count() -> int:
    return os.cpu_count() or 1


def optimal_num_workers():
    cpu_count = _cpu_count()
    num_workers = max(1, math.floor(cpu_count - 2))
    return num_workers
