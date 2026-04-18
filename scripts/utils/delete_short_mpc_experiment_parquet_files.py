import shutil
from collections import Counter
from pathlib import Path

import pandas as pd

from alphabuilding.utils.paths import paths

SHORT_SIMULATION_HOURS_THRESHOLD = 72

mpc_experiments_dir = paths.mpc_experiments_dir
files = list(mpc_experiments_dir.glob("*/*.parquet"))

print(f"Total files: {len(files)}")

length_hours_by_file = {}
short_files = []

for file in files:
    df = pd.read_parquet(file)
    length_hours = (df.index[-1] - df.index[0]).total_seconds() / 3600.0
    length_hours_by_file[file] = length_hours

    if length_hours < SHORT_SIMULATION_HOURS_THRESHOLD:
        short_files.append(file)

print(f"Total short files (<{SHORT_SIMULATION_HOURS_THRESHOLD}h): {len(short_files)}")

# Count files by duration
length_int = {f: int(round(h)) for f, h in length_hours_by_file.items()}
counts = Counter(length_int.values())

print("\nCounts by (rounded) duration in hours:")
for h in sorted(counts):
    print(f"{h:4d} h : {counts[h]} files")

# ---- Find parent directories with no parquet files ----
# Assuming structure: mpc_experiments_dir / <experiment_dir> / ...
all_top_level_dirs = [d for d in mpc_experiments_dir.iterdir() if d.is_dir()]

dirs_without_parquet = []
for d in all_top_level_dirs:
    has_parquet = any(p.suffix == ".parquet" for p in d.rglob("*"))
    if not has_parquet:
        dirs_without_parquet.append(d)

print(f"\nTop-level directories: {len(all_top_level_dirs)}")
print(
    f"Directories without any .parquet (will be candidates for deletion): {len(dirs_without_parquet)}"
)

if dirs_without_parquet:
    print("\nDirectories without parquet:")
    for d in dirs_without_parquet:
        print(f"  {d}")

    confirm_dirs = input(
        f"\nDelete these {len(dirs_without_parquet)} directories (recursively)? y/n "
    )
    if confirm_dirs.lower() == "y":
        for d in dirs_without_parquet:
            print(f"Deleting directory tree: {d}")
            shutil.rmtree(d)
        print("Directory deletion complete.")
    else:
        print("Directory deletion cancelled.")
else:
    print("No directories without parquet files found.")

# ---- Delete short files (as before) ----
if short_files:
    confirm = input(
        f"\nAre you sure you want to delete {len(short_files)} short files? y/n "
    )
    if confirm.lower() == "y":
        for file in short_files:
            print(f"Deleting file: {file}")
            file.unlink()
        print("Deletion complete.")
    else:
        print("Deletion cancelled.")
else:
    print("No short files to delete.")
