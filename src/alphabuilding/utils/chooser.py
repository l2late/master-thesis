import json
import time
from pathlib import Path

import questionary
from iterfzf import iterfzf
from prompt_toolkit.completion import FuzzyWordCompleter
from questionary import Choice

# Required artifacts inside a run directory
REQUIRED_CHECKPOINT = Path("checkpoints") / "last.ckpt"
REQUIRED_CONFIG = Path(".hydra") / "config.yaml"

# Where to persist the last selection
CACHE_FILE = Path.home() / ".cache" / "run_selector_last.json"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_last_used(cache_file: Path = CACHE_FILE) -> Path | None:
    try:
        data = json.loads(cache_file.read_text())
        p = Path(data.get("last_dir", "")).expanduser().resolve()
        return p if p.exists() else None
    except Exception:
        return None


def save_last_used(run_dir: Path, cache_file: Path = CACHE_FILE) -> None:
    _ensure_parent(cache_file)
    cache_file.write_text(json.dumps({"last_dir": str(run_dir)}))


def is_valid_run_dir(p: Path) -> bool:
    return (p / REQUIRED_CHECKPOINT).is_file() and (p / REQUIRED_CONFIG).is_file()


def list_candidate_runs(runs_root: Path, limit: int = 200) -> list[tuple[Path, float]]:
    """
    Find run directories under runs_root that contain both required files.
    Returns list of (run_dir, score) sorted by most recent checkpoint mtime.
    """
    candidates = {}
    for ckpt in runs_root.rglob(str(REQUIRED_CHECKPOINT)):
        run_dir = ckpt.parent.parent
        cfg = run_dir / REQUIRED_CONFIG
        if cfg.is_file():
            # score by checkpoint mtime; newer first
            candidates[run_dir] = ckpt.stat().st_mtime
    # sort by mtime desc and cap
    sorted_runs = sorted(candidates.items(), key=lambda kv: kv[1], reverse=True)
    return sorted_runs[:limit]


def validate_run_dir_for_prompt(text: str):
    """
    questionary.validate-compatible validator for the path prompt.
    Must return True or an error message string.
    """
    if not text:
        return "Please provide a directory path"
    p = Path(text).expanduser()
    if not p.exists():
        return f"Not found: {p}"
    if not p.is_dir():
        return f"Not a directory: {p}"
    if not (p / REQUIRED_CHECKPOINT).is_file():
        return f"Missing {REQUIRED_CHECKPOINT} under {p}"
    if not (p / REQUIRED_CONFIG).is_file():
        return f"Missing {REQUIRED_CONFIG} under {p}"
    return True


from questionary import Style

RUN_SELECT_STYLE = Style(
    [
        ("pointer", "fg:#00ff00 bold"),  # arrow in front of current line
        ("highlighted", "fg:#ffffff bg:#444444 bold"),  # current line
        ("selected", "fg:#00ff00 bold"),  # line after pressing Enter (optional)
    ]
)


def choose_run_dir(
    runs_root: Path,
    title: str = "Select a run directory",
    allow_browse: bool = True,
    auto_select_last: bool = False,  # New parameter
) -> Path:
    """
    Interactively choose a run directory that contains the required files.
    - shows discovered runs under runs_root
    - promotes last used to the top and preselects it
    - offers a Browse option to pick any directory

    Args:
        runs_root: Root directory to search for runs
        title: Title for the interactive prompt
        allow_browse: Whether to show browse option
        auto_select_last: If True, automatically selects last used directory without interaction
    """
    last_used = load_last_used()

    # Auto-select last used if requested and valid
    if auto_select_last and last_used and is_valid_run_dir(last_used):
        print(f"Auto-selecting last used directory: {last_used}")
        save_last_used(last_used)  # Update timestamp
        return last_used

    # If auto-select was requested but no valid last used, show warning and continue with interactive mode
    if auto_select_last and (not last_used or not is_valid_run_dir(last_used)):
        print(
            "Warning: Auto-select requested but no valid last used directory found. Falling back to interactive mode."
        )

    discovered = list_candidate_runs(Path(runs_root))

    # Build choice list
    choices: list[Choice] = []
    # Promote last used if it is valid (and optionally exists outside runs_root)
    if last_used and is_valid_run_dir(last_used):
        choices.append(Choice(title=f"Last used • {last_used}", value=last_used))

    # Add discovered runs (avoid duplicating the last used)
    seen = set()
    if last_used:
        seen.add(last_used.resolve())
    for run_dir, mtime in discovered:
        if run_dir.resolve() in seen:
            continue
        # show relative path label if under runs_root for readability
        try:
            label = str(run_dir.relative_to(runs_root))
        except Exception:
            label = str(run_dir)
        human_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
        choices.append(Choice(title=f"{label} • {human_time}", value=run_dir))
        seen.add(run_dir.resolve())

    # Optionally allow browsing
    BROWSE = "__BROWSE__"
    if allow_browse:
        choices.append(Choice(title="Browse for directory…", value=BROWSE))

    # If nothing discovered, force browse path
    if not choices:
        browsed = questionary.path(
            "Browse to a valid run directory",
            only_directories=True,
            validate=validate_run_dir_for_prompt,
        ).ask()
        if browsed is None:
            raise KeyboardInterrupt("Cancelled by user")
        run_dir = Path(browsed).expanduser().resolve()
        save_last_used(run_dir)
        return run_dir

    # Default selection points to last used when present
    default_value = last_used if (last_used and is_valid_run_dir(last_used)) else None

    choice_map = {c.title: c.value for c in choices}

    selected_title = iterfzf(choice_map.keys(), prompt=title + "> ", sort=True)

    if not selected_title:
        raise KeyboardInterrupt("Cancelled")

    run_dir = choice_map[selected_title]
    save_last_used(run_dir)
    return run_dir
