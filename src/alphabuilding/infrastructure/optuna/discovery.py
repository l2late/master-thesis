"""Auto-discover and pair Optuna MPC ↔ RBC study databases by shared run_id suffix."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)

# Patterns that match study names like "mpc_tuning_itqhw9m6" / "rbc_tuning_abc123"
_RE_RUN_ID = re.compile(r"^(?P<kind>mpc|rbc)_tuning_(?P<run_id>.+)$")


@dataclass(frozen=True)
class PairedStudies:
    """MPC and RBC studies that share the same model run_id."""

    run_id: str
    mpc_db: Path
    mpc_study: str
    rbc_db: Path
    rbc_study: str

    @property
    def db_set(self) -> set[Path]:
        return {self.mpc_db, self.rbc_db}


def find_paired_studies(hopt_dir: Path | str) -> list[PairedStudies]:
    """
    Scan *hopt_dir* (recursively) for Optuna database files. Inspect each DB
    for studies matching ``<kind>_tuning_<run_id>`` and return every (MPC, RBC)
    pair that shares the same run_id.

    Parameters
    ----------
    hopt_dir : Path or str
        Root directory to search. Typically a folder containing subdirectories
        from extracted cloud hopt tarballs.

    Returns
    -------
    list[PairedStudies]
        All complete pairs found.  May be empty if no matching pair exists.
    """
    hopt_dir = Path(hopt_dir)

    # ── Step 1: discover all DB files ──────────────────────────────
    db_files = sorted(hopt_dir.rglob("*.db"))
    if not db_files:
        raise FileNotFoundError(
            f"No .db files found under {hopt_dir}. "
            f"Did you extract the hopt output directories?"
        )

    # ── Step 2: catalogue studies by (kind, run_id) → (db, study_name) ──
    mpc: dict[str, tuple[Path, str]] = {}
    rbc: dict[str, tuple[Path, str]] = {}

    for db_file in db_files:
        try:
            storage = f"sqlite:///{db_file}"
            summaries = optuna.get_all_study_summaries(storage=storage)
        except Exception:
            # Skip corrupted or non-SQLite DBs gracefully
            continue

        for s in summaries:
            m = _RE_RUN_ID.match(s.study_name)
            if not m:
                continue
            kind, run_id = m.group("kind"), m.group("run_id")
            entry = (db_file, s.study_name)
            if kind == "mpc":
                mpc[run_id] = entry
            elif kind == "rbc":
                rbc[run_id] = entry

    # ── Step 3: pair by intersection of run_ids ────────────────────
    paired_run_ids = sorted(set(mpc) & set(rbc))
    return [
        PairedStudies(
            run_id=rid,
            mpc_db=mpc[rid][0],
            mpc_study=mpc[rid][1],
            rbc_db=rbc[rid][0],
            rbc_study=rbc[rid][1],
        )
        for rid in paired_run_ids
    ]
