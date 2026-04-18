import re
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.linalg import cond, matrix_power, matrix_rank
from omegaconf import OmegaConf
from tbparse import SummaryReader

from analysis.convert_table_to_image import latex_table_to_image
from alphabuilding.utils.paths import paths
from eval import (
    analyze_discrete_gramian_properties,
)
from utils.instantiation import init_module_trained_from_cfg
from utils.state_space import (
    discretize_system,
    get_continuous_A_B_C_D_from_dynamics_module,
)


def export_to_latex(df: pd.DataFrame, output_path: Path, n_lowest_bold: int = 3):
    """
    Exports the analysis results to a formatted LaTeX table.
    n_lowest_bold: Number of lowest RMSE values to highlight with bold formatting.
    """
    # 1. Create a copy to avoid modifying the original dataframe
    tex_df = df.copy()

    # 2. Sort by Model Order first, then Tmargin
    tex_df = tex_df.sort_values(by=["num_latent_states", "Tmargin"])

    # Identify indices of the N lowest RMSE values
    best_indices = set()
    if n_lowest_bold > 0 and "rmse" in tex_df.columns:
        # nsmallest handles ties by index order by default; can use keep='all' if desired
        best_indices = set(tex_df.nsmallest(n_lowest_bold, "rmse").index)

    # 3. Format Helper Functions
    def fmt_sci(x):
        """Formats large numbers as LaTeX scientific notation."""
        if pd.isna(x) or x is None:
            return "-"
        if x > 1000 or (0 < x < 0.01):
            s = "{:.1e}".format(x)
            base, exponent = s.split("e")
            return f"${base} \\times 10^{{{int(exponent)}}}$"
        return f"${x:.1f}$"

    def fmt_rmse_row(row):
        """Formats RMSE with bolding for best values."""
        x = row["rmse"]
        if pd.isna(x):
            return "-"
        val_str = f"{x:.4f}"

        # Check if this row is among the best indices
        if row.name in best_indices:
            # Use \textbf for bold text mode (standard for highlighting in tables)
            return f"\\textbf{{{val_str}}}"

        return f"${val_str}$"

    # 4. Apply Formatting
    # Rename columns for the LaTeX header mapping
    tex_df["n_l"] = tex_df["num_latent_states"]
    tex_df["T_m"] = tex_df["Tmargin"]

    # Apply row-wise formatting for RMSE to access the index for bolding logic
    tex_df["RMSE"] = tex_df.apply(fmt_rmse_row, axis=1)

    # Process Condition Numbers
    # tex_df["Cond_Obsv"] = tex_df["cond_obsv"].apply(fmt_sci)
    # tex_df["Cond_Ctrb"] = tex_df["cond_ctrb"].apply(fmt_sci)

    # Gramian condition numbers
    tex_df["Gram_Cond_Obsv"] = tex_df["gramian_cond_obsv"].apply(fmt_sci)
    tex_df["Gram_Cond_Ctrb"] = tex_df["gramian_cond_cont"].apply(fmt_sci)

    # Clean up Rank strings (optional: remove the "/n" if redundant)
    # Keeping it is fine, but wrapping in math mode looks better
    tex_df["Rank_Obsv"] = tex_df["rank_obsv_str"].apply(lambda x: f"${x}$")
    tex_df["Rank_Ctrb"] = tex_df["rank_ctrb_str"].apply(lambda x: f"${x}$")

    # 5. Select and Rename Columns for the final table
    final_df = tex_df[
        [
            "n_l",
            "T_m",
            "RMSE",
            "Rank_Obsv",
            # "Cond_Obsv",
            "Gram_Cond_Obsv",
            "Rank_Ctrb",
            # "Cond_Ctrb",
            "Gram_Cond_Ctrb",
        ]
    ]

    # 6. Generate LaTeX String manually for full control over headers/booktabs
    # We build the body row by row
    rows = []
    for _, row in final_df.iterrows():
        row_str = " & ".join([str(x) for x in row.values])
        rows.append(f"{row_str} \\\\")

    latex_content = r"""
\caption{Performance and Structural Properties of Identified Models. $n_l$ is the number of latent states, $T_{\mathrm{margin}}$ is the $\pm$ temperature margin around the Hysteresis setpoint where a input PRBS signal is applied, and the observability and controllability metrics indicate the structural properties of the identified state-space models. RMSE is computed on the validation set.}
\label{tab:model_analysis}
\begin{tabular}{cc c cc cc}
\toprule
\multicolumn{2}{c}{Parameters} & \multicolumn{1}{c}{Performance} & \multicolumn{2}{c}{Observability} & \multicolumn{2}{c}{Controllability} \\
\cmidrule(lr){1-2} \cmidrule(lr){3-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7}
$n_l$ & $T_{\mathrm{margin}}$ & RMSE ($^\circ$C) & Rank & $\kappa(W_{\mathcal{O}})$ & Rank & $\kappa(W_{\mathcal{C}})$ \\
\midrule
"""
    latex_content += "\n".join(rows)
    latex_content += r"""
\bottomrule
\end{tabular}
"""

    with open(str(output_path), "w") as f:
        f.write(latex_content)

    print(f"LaTeX table saved to {output_path}")


def parse_dir_info(dir_name):
    """Extracts Tmargin and num_latent_states from directory name."""
    tmargin_match = re.search(r"Tmargin_([0-9\.]+)", dir_name)
    latents_match = re.search(r"num_latent_states=(\d+)", dir_name)

    if tmargin_match and latents_match:
        return {
            "Tmargin": float(tmargin_match.group(1)),
            "num_latent_states": int(latents_match.group(1)),
        }
    return None


def get_best_rmse(log_dir):
    """Extracts best RMSE from TensorBoard logs."""
    try:
        log_path = Path(log_dir)
        # Find events file recursively
        event_files = list(log_path.rglob("events.out.tfevents.*"))
        if not event_files:
            return None

        reader = SummaryReader(str(event_files[0].parent))
        df = reader.scalars
        metric_data = df[df["tag"] == "val/rmse_celsius"]

        if not metric_data.empty:
            return metric_data["value"].min()
    except Exception:
        # print(f"TB Parse Error for {log_dir}: {e}")
        pass
    return None


def analyze_model_properties(run_dir):
    """
    Loads the checkpoint, extracts A, B, C matrices, and computes
    observability and controllability metrics.
    """
    run_path = Path(run_dir)
    ckpt_path = run_path / "checkpoints" / "last.ckpt"
    config_path = run_path / ".hydra" / "config.yaml"

    if not ckpt_path.exists() or not config_path.exists():
        return None

    try:
        cfg = OmegaConf.load(config_path)

        # Load Model
        module = init_module_trained_from_cfg(cfg, ckpt_path)
        module.eval()  # Set to eval mode

        # Extract Matrices (Continuous)
        A_c, B_c, C, D = get_continuous_A_B_C_D_from_dynamics_module(module.dynamics)

        dt_hours = 0.25
        A_d, B_d = discretize_system(A_c, B_c, C, dt_hours=dt_hours)

        discrete_gramian_cond_numbers = analyze_discrete_gramian_properties(A_d, B_d, C)

        n = A_d.shape[0]

        # --- Controllability using (Control Inputs only, first 5 cols) ---
        B_control = B_d[:, :5]

        Ctrb = B_control
        for i in range(1, n):
            Ctrb = np.hstack((Ctrb, matrix_power(A_d, i) @ B_control))

        rank_ctrb = matrix_rank(Ctrb)
        cond_ctrb = cond(Ctrb)

        # --- Observability ---
        Obsv = C
        for i in range(1, n):
            Obsv = np.vstack((Obsv, C @ matrix_power(A_d, i)))

        rank_obsv = matrix_rank(Obsv)
        cond_obsv = cond(Obsv)

        return {
            "rank_ctrb_val": rank_ctrb,
            "rank_ctrb_str": f"{rank_ctrb}/{n}",
            "cond_ctrb": cond_ctrb,
            "rank_obsv_val": rank_obsv,
            "rank_obsv_str": f"{rank_obsv}/{n}",
            "cond_obsv": cond_obsv,
            "gramian_cond_cont": discrete_gramian_cond_numbers["cond_ctrb"],
            "gramian_cond_obsv": discrete_gramian_cond_numbers["cond_obsv"],
        }

    except Exception as e:
        print(f"Error analyzing model at {run_dir}: {e}")
        return None


def find_run_directories(base_path: Path) -> list[Path]:
    """
    Recursively finds all run directories that contain the required files.
    A valid run directory must have:
    - checkpoints/last.ckpt
    - .hydra/config.yaml
    - events files (for TensorBoard logs)
    """
    run_dirs = []

    # Check if base_path itself is a multirun directory
    if (base_path / "multiruns").exists():
        # Search within all multirun subdirectories
        for multirun_dir in (base_path / "multiruns").iterdir():
            if multirun_dir.is_dir():
                run_dirs.extend(_find_valid_runs(multirun_dir))
    elif base_path.name.startswith("multiruns") or _is_valid_run(base_path.parent):
        # base_path points directly to a multirun directory
        run_dirs.extend(_find_valid_runs(base_path))
    else:
        # Search recursively from base_path
        run_dirs.extend(_find_valid_runs(base_path))

    return run_dirs


def _is_valid_run(run_dir: Path) -> bool:
    """Check if a directory contains required checkpoint and config files."""
    return (run_dir / "checkpoints" / "last.ckpt").exists() and (
        run_dir / ".hydra" / "config.yaml"
    ).exists()


def _find_valid_runs(search_path: Path) -> list[Path]:
    """
    Recursively search for valid run directories within search_path.
    Stops searching deeper once a valid run is found.
    """
    valid_runs = []

    for item in search_path.iterdir():
        if not item.is_dir():
            continue

        # Check if this directory is a valid run
        if _is_valid_run(item):
            valid_runs.append(item)
            # Don't search deeper - we found a run directory
        else:
            # Recursively search subdirectories
            valid_runs.extend(_find_valid_runs(item))

    return valid_runs


def process_all_runs(base_dir, limit=None):
    base_path = Path(base_dir)
    results = []

    print(f"Scanning {base_path}...")

    # Find all valid run directories recursively
    all_runs = find_run_directories(base_path)
    all_runs = sorted(all_runs)
    print(f"Found {len(all_runs)} valid run directories")

    count = 0
    for run_dir in all_runs:
        # Stop if we hit the limit
        if limit is not None and count >= limit:
            print(f"Limit of {limit} reached.")
            break

        params = parse_dir_info(run_dir.name)
        if not params:
            print(f"  Skipping {run_dir.name} - couldn't parse parameters")
            continue

        print(
            f"[{count + 1}] Processing: Tmargin={params['Tmargin']}, Latents={params['num_latent_states']}"
        )

        rmse = get_best_rmse(run_dir)

        struct_props = analyze_model_properties(run_dir)

        # Combine data
        entry = params.copy()
        entry["rmse"] = rmse

        if struct_props:
            entry.update(struct_props)
        else:
            # Fill with N/A if model load failed
            entry.update(
                {
                    "rank_ctrb_str": "N/A",
                    "cond_ctrb": None,
                    "rank_obsv_str": "N/A",
                    "cond_obsv": None,
                    "gramian_cond_cont": None,
                    "gramian_cond_obsv": None,
                }
            )

        results.append(entry)
        count += 1

    return pd.DataFrame(results)


if __name__ == "__main__":
    logdir_name = "linear_discrete_observer_metzler_masked_1to1_reset"
    # logdir_name = "linear_discrete_observer_metzler_masked_1tomany_better_init"
    # logdir_name = "linear_discrete_observer_metzler_masked_1tomany_reset_better_init_1"
    # logdir_name = "linear_discrete_observer_metzler_masked_1tomany_mse"
    # logdir_name = (
    #     "linear_discrete_observer_metzler_masked_1to1_mse"  # can't parse parameters
    # )
    # logdir_name = "linear_discrete_observer_metzler_masked_1to1_better_init"
    LOGS_DIR = Path(paths.log_dir) / "vastai" / logdir_name
    analysis_filename = f"{logdir_name}_analysis_results"
    analysis_filename_csv = Path(paths.output_dir) / f"{analysis_filename}.csv"

    # Set limit=None to process everything, or an integer (e.g., 5) for testing
    TEST_LIMIT = None
    process = True  # Set to False to load precomputed results

    if process == True:
        df = process_all_runs(LOGS_DIR, limit=TEST_LIMIT)
        if not df.empty:
            # Reorder columns nicely
            cols = [
                "Tmargin",
                "num_latent_states",
                "rmse",
                "rank_obsv_str",
                "cond_obsv",
                "rank_ctrb_str",
                "cond_ctrb",
                "gramian_cond_obsv",
                "gramian_cond_cont",
            ]
            # Only select columns that actually exist (in case of partial failures)
            present_cols = [c for c in cols if c in df.columns]
            df = df[present_cols]

            print("\n" + "=" * 80)
            print("ANALYSIS RESULTS DATAFRAME")
            print("=" * 80)
            print(df.to_string(index=False, float_format="%.4f"))
            print("=" * 80)

            # Export
            df.to_csv(analysis_filename_csv, index=False)
            print("\nSaved to full_analysis_results.csv")
        else:
            print("No results found.")
    else:
        # Load precomputed results for faster iteration
        df = pd.read_csv(analysis_filename_csv)

    if not df.empty:
        tex_output_path = Path(paths.output_dir) / f"{analysis_filename}.tex"
        export_to_latex(df, output_path=tex_output_path)
        print("\nGenerated LaTeX table at:", tex_output_path)
        # Optionally convert to image
        latex_content = tex_output_path.read_text()
        image_output_path = Path(paths.output_dir) / f"{analysis_filename}.png"
        latex_table_to_image(latex_content, image_output_path, dpi=300)
