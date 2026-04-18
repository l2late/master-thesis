from pathlib import Path

import pandas as pd
from tbparse import SummaryReader


def get_best_metric_value(log_dir, metric_name, mode="min"):
    """Extract the best value of a specific metric from TensorBoard logs."""
    try:
        reader = SummaryReader(str(log_dir))
        df = reader.scalars

        # Filter for the specific metric
        metric_data = df[df["tag"] == metric_name]

        if len(metric_data) > 0:
            if mode == "min":
                best_value = metric_data["value"].min()
            elif mode == "max":
                best_value = metric_data["value"].max()
            else:
                raise ValueError("Mode must be 'min' or 'max'")
            return best_value
        else:
            return None
    except Exception as e:
        print(f"Error processing {log_dir}: {e}")
        return None


def get_last_metric_value(log_dir, metric_name):
    """Extract the last value of a specific metric from TensorBoard logs."""
    try:
        reader = SummaryReader(str(log_dir))
        df = reader.scalars

        # Filter for the specific metric
        metric_data = df[df["tag"] == metric_name].sort_values("step")

        if len(metric_data) > 0:
            return metric_data.iloc[-1]["value"]
        else:
            return None
    except Exception as e:
        print(f"Error processing {log_dir}: {e}")
        return None


def create_rmse_table(base_log_dir, log_dirs, labels, metric_name="rmse_celsius"):
    """Create a table with the last RMSE values from multiple runs."""
    results = []

    for log_dir, label in zip(log_dirs, labels):
        full_path = Path(base_log_dir) / log_dir
        # last_value = get_last_metric_value(full_path, metric_name)
        last_value = get_best_metric_value(full_path, metric_name, mode="min")

        results.append(
            {
                "Configuration": label,
                f"Lowest {metric_name} (°C)": f"{last_value:.4f}"
                if last_value is not None
                else "N/A",
                # "Raw Value": last_value,
            }
        )

    df = pd.DataFrame(results)
    return df


def export_for_presentations(df, output_dir="tables", base_name="rmse_comparison"):
    """Export table in multiple presentation-ready formats."""
    output_dir = Path(output_dir)
    assert output_dir.is_dir(), (
        f"Output directory {output_dir} must be a directory or not exist."
    )
    # output_dir.mkdir(exist_ok=True)

    print(f"\nExporting to {output_dir}/...")

    # 1. LaTeX for Beamer
    latex_path = output_dir / f"{base_name}.tex"
    latex_table = df.to_latex(
        index=False,
        float_format="%.3f",
        caption="Lowest RMSE (°C) comparison across different model configurations",
        label="tab:rmse_comparison",
        column_format="lc",
        escape=False,
    )
    with open(latex_path, "w") as f:
        f.write(latex_table)
    print(f"✓ LaTeX: {latex_path}")

    # 2. CSV for PowerPoint
    csv_path = output_dir / f"{base_name}.csv"
    df.to_csv(csv_path, index=False, float_format="%.3f")
    print(f"✓ CSV: {csv_path}")

    # 5. Print formatted
    print("\n" + "=" * 60)
    print("FORMATTED TABLE:")
    print("=" * 60)
    print(df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("=" * 60)


# Usage with your paths:
if __name__ == "__main__":
    # from analysis.midterm_plot_configs import plot_configs
    from alphabuilding.utils.paths import paths

    base_dir = Path(paths.log_dir) / "vastai/linear_discrete_observer_metzler_all"
    log_dirs = base_dir.iterdir()

    all_log_dirs = []
    all_labels = []

    for config in plot_configs:
        for log_dir, label in zip(config.log_dirs, config.labels):
            # Avoid duplicates
            if log_dir not in all_log_dirs:
                all_log_dirs.append(log_dir)
                all_labels.append(label)

    rmse_table = create_rmse_table(
        base_log_dir="",
        log_dirs=all_log_dirs,
        labels=all_labels,
        metric_name="val/rmse_celsius",
    )
    print(rmse_table)

    # export_for_presentations(
    #     rmse_table,
    #     output_dir=paths.root_dir / "tables",
    #     base_name="val_rmse_comparison",
    # )

    # # Display the table
    # print("\n" + "=" * 70)
    # print("Final RMSE Values from Training Logs")
    # print("=" * 70)
    # print(rmse_table.to_string(index=False))
    # print("=" * 70)
    #
    # # Save to CSV
    # rmse_table.to_csv(
    #     paths.root_dir / "figures" / "val_rmse_comparison.csv", index=False
    # )
    # print(f"\nTable saved to: {paths.root_dir / 'figures' / 'val_rmse_comparison.csv'}")
    #
    # # Markdown format
    # print("\n" + "=" * 70)
    # print("Markdown Format:")
    #
    # print(
    #     rmse_table[["Configuration", "Final rmse_celsius (°C)"]].to_markdown(
    #         index=False
    #     )
    # )
