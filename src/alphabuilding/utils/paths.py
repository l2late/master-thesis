import re
from dataclasses import dataclass
from pathlib import Path

from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf

from alphabuilding.infrastructure.omegaconf.resolvers import register_resolvers

register_resolvers()


@dataclass
class PathsConfig:
    data_dir: str = "${path:data}"
    log_dir: str = "${path:logs}"
    output_dir: str = "${path:output}"
    test_data_dir: str = "${path:tests/data}"
    cache_dir: str = "${path:.cache}"
    sinergym_dir: str = "${path:sinergym}"
    tables_dir: str = "${path:output/tables}"
    figures_dir: str = "${path:output/figures}"
    mpc_experiments_dir: str = "${path:output/controller_experiments/mpc}"
    rbc_experiments_dir: str = "${path:output/controller_experiments/rbc}"
    mpc_sweeps_dir: str = "${path:output/mpc_experiments}"
    artifact_dir: str = "${path:output/artifacts}"
    # TODO: Remove this hardcoded path. It would be nice to have a more robust way to manage this path, since it user-specific and may not even exist on the current machine.
    report_results_dir: str = (
        "${path:../../../../LaTeX/master-thesis-final-report/results}"
    )


cs = ConfigStore.instance()
cs.store(group="paths", name="default", node=PathsConfig)


def get_paths_config():
    # returns a dataclass-like object whose attributes are resolved to Paths
    cfg = OmegaConf.structured(PathsConfig())
    # 2. Resolve all interpolations
    OmegaConf.resolve(cfg)
    # 3. Convert back to a plain dataclass-like object if you want
    return OmegaConf.to_object(cfg)


paths = get_paths_config()


def get_latest_mpc_sweep_run_dir(
    base_dir: Path | str = paths.mpc_sweeps_dir,
) -> Path | None:
    """
    Returns the path to the most recent directory formatted as YYYYMMDD-HHMMSS.
    Returns None if no matching directories are found.
    """
    base_path = Path(base_dir)

    if not base_path.exists() or not base_path.is_dir():
        return None

    # Matches exactly 8 digits, a hyphen, and 6 digits
    pattern = re.compile(r"^\d{8}-\d{6}$")

    # Filter for directories that strictly match the naming convention
    valid_dirs = [
        d for d in base_path.iterdir() if d.is_dir() and pattern.match(d.name)
    ]

    if not valid_dirs:
        return None

    # Since alphabetical order is chronological for this format,
    # max() instantly finds the newest string.
    return max(valid_dirs, key=lambda p: p.name)
