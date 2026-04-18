from pathlib import Path

from omegaconf import OmegaConf

from alphabuilding.project_root import ROOT


def shortened_resolver(string):
    """
    Shortens a Hydra override string to fit in Linux filename limits.
    1. Splits overrides by comma.
    2. Reduces file paths to just filenames (e.g., /long/path/file.csv -> file.csv).
    3. Truncates result if still > 240 chars.
    """
    # Convert to string (Hydra sometimes passes non-strings)
    s = str(string)

    # Split by comma (Hydra's default separator for overrides)
    items = s.split(",")

    final_items = []
    for item in items:
        # Check if item is a key=value pair
        if "=" in item:
            key, val = item.split("=", 1)
            # If value looks like a path (contains slashes), keep only the filename
            if "/" in val:
                val = Path(val).name
            final_items.append(f"{key}={val}")
        else:
            final_items.append(item)

    # Rejoin with underscores for a safe, flat directory name
    result = "_".join(final_items)

    # Safety valve: Hash if still too long (Linux limit is 255)
    if len(result) > 240:
        import hashlib

        # Keep the first 200 chars for readability, append short hash for uniqueness
        h = hashlib.md5(result.encode()).hexdigest()[:8]
        return f"{result[:200]}_md5_{h}"

    return result


def absolute_path_resolver(string):
    """
    Resolves a relative path to an absolute path.
    Useful for ensuring file paths are consistent regardless of the current working directory.
    """
    return str(Path(string).expanduser().resolve())


def register_resolvers() -> None:
    OmegaConf.register_new_resolver("shorten_path", shortened_resolver)
    OmegaConf.register_new_resolver(
        "path",
        lambda rel: ROOT / rel,
        replace=True,
    )
