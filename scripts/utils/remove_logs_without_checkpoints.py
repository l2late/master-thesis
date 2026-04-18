"""Clean timestamped log directories that lack model checkpoints.

The utility inspects timestamp-named Hydra/Lightning run directories under a
logs root and removes those that never produced checkpoints. If a run contains a
`checkpoints` directory anywhere under the timestamped folder, the run is
preserved. The tool never deletes the contents of `lightning_logs` directly and
operates in dry-run mode by default so you can review actions first.

Example usage (from the project root)::

    python scripts/remove_logs_without_checkpoints.py --apply

"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
from pathlib import Path
from typing import Iterable, Sequence

LOGGER = logging.getLogger(__name__)

RUN_DIR_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")


def _default_logs_path() -> Path:
    return Path(__file__).resolve().parents[1] / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete log directories that do not contain checkpoints."
    )
    parser.add_argument(
        "--logs-path",
        type=Path,
        default=_default_logs_path(),
        help="Root directory containing training logs (default: %(default)s)",
    )
    parser.add_argument(
        "--min-checkpoints",
        type=int,
        default=1,
        help="Minimum number of checkpoint files required to keep a run (default: %(default)d)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete directories. Without this flag the command only reports actions.",
    )
    parser.add_argument(
        "--prune-empty-parents",
        action="store_true",
        help="After removing a run directory, also remove any now-empty parent folders under the logs root.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging the cleanup process.",
    )
    return parser.parse_args()


def resolve_logs_path(logs_path: Path) -> Path:
    expanded = logs_path.expanduser().resolve()
    if not expanded.exists():
        raise FileNotFoundError(f"Logs path '{expanded}' does not exist")
    if not expanded.is_dir():
        raise NotADirectoryError(f"Logs path '{expanded}' is not a directory")
    return expanded


def find_candidate_run_dirs(logs_path: Path) -> set[Path]:
    """Return timestamped run directories that should be inspected."""
    candidates: set[Path] = set()

    for directory in logs_path.rglob("*"):
        if not directory.is_dir():
            continue
        if "lightning_logs" in directory.parts:
            # Never act directly on lightning_logs contents.
            continue
        if RUN_DIR_PATTERN.fullmatch(directory.name):
            candidates.add(directory)

    return candidates


def collect_checkpoint_files(run_dir: Path) -> list[Path]:
    return [path for path in run_dir.rglob("*.ckpt") if path.is_file()]


def has_checkpoint_directory(run_dir: Path) -> bool:
    return any(path.is_dir() for path in run_dir.rglob("checkpoints"))


def prune_empty_parents(path: Path, stop: Path) -> list[Path]:
    """Remove empty parent directories up to, but not including, ``stop``."""
    removed: list[Path] = []
    current = path.resolve().parent
    stop = stop.resolve()

    while current != stop and stop in current.parents:
        try:
            next(current.iterdir())
        except StopIteration:
            shutil.rmtree(current)
            removed.append(current)
            current = current.parent
        else:
            break

    return removed


def sort_by_depth(paths: Iterable[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: len(path.resolve().parts), reverse=True)


def remove_directories(
    directories: Sequence[Path],
    *,
    apply: bool,
    prune: bool,
    logs_root: Path,
) -> None:
    sorted_directories = sort_by_depth(directories)
    for run_dir in sorted_directories:
        if "lightning_logs" in run_dir.parts:
            LOGGER.warning(
                "Skipping %s because it resides inside a lightning_logs directory",
                run_dir,
            )
            continue
        if apply:
            LOGGER.info("Removing %s", run_dir)
            shutil.rmtree(run_dir, ignore_errors=False)
            if prune:
                removed_parents = prune_empty_parents(run_dir, logs_root)
                for parent in removed_parents:
                    LOGGER.info("Pruned empty parent %s", parent)
        else:
            LOGGER.info("[dry-run] Would remove %s", run_dir)


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    try:
        logs_path = resolve_logs_path(args.logs_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        LOGGER.error("%s", exc)
        return 1

    candidate_run_dirs = find_candidate_run_dirs(logs_path)
    if not candidate_run_dirs:
        LOGGER.info("No run directories found under %s", logs_path)
        return 0

    directories_without_checkpoints = []
    min_required = max(args.min_checkpoints, 0)
    for run_dir in sorted(candidate_run_dirs):
        if has_checkpoint_directory(run_dir):
            LOGGER.debug("Skipping %s (contains checkpoints directory)", run_dir)
            continue

        checkpoint_files = collect_checkpoint_files(run_dir)
        if len(checkpoint_files) >= min_required:
            LOGGER.debug(
                "Skipping %s (found %d checkpoint files)",
                run_dir,
                len(checkpoint_files),
            )
            continue
        directories_without_checkpoints.append(run_dir)

    if not directories_without_checkpoints:
        LOGGER.info("No directories without checkpoints detected under %s", logs_path)
        return 0

    LOGGER.info(
        "Identified %d directories without checkpoints:",
        len(directories_without_checkpoints),
    )
    for run_dir in sorted(directories_without_checkpoints):
        LOGGER.info("  %s", run_dir)

    remove_directories(
        directories_without_checkpoints,
        apply=args.apply,
        prune=args.prune_empty_parents,
        logs_root=logs_path,
    )

    if not args.apply:
        LOGGER.info("Dry-run complete. Re-run with --apply to delete the directories.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
