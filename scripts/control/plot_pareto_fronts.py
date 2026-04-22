"""Plot and save Pareto-dominant fronts for paired MPC/RBC hopt studies.

Usage
-----
    uv run python scripts/control/plot_pareto_fronts.py --hopt-dir output/eval_hopt/
    uv run python scripts/control/plot_pareto_fronts.py --help
"""

import argparse
import os
from pathlib import Path

import optuna

from alphabuilding.infrastructure.optuna.discovery import find_paired_studies
from alphabuilding.infrastructure.optuna.study_analysis import get_sorted_best_trials
from alphabuilding.infrastructure.optuna.visualization import (
    MPC_STYLE,
    RBC_STYLE,
    ParetoStudy,
    plot_pareto_dominant,
)
from alphabuilding.utils.paths import paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot Pareto-dominant fronts for paired MPC/RBC hopt studies.",
    )
    default_hopt_dir = Path(
        os.environ.get("HOPT_DIR", str(Path(paths.output_dir) / "eval_hopt"))
    )
    parser.add_argument(
        "--hopt-dir",
        type=Path,
        default=default_hopt_dir,
        help=(
            "Directory to scan for paired Optuna .db files. "
            "Default: $HOPT_DIR or output/eval_hopt."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=("Directory to save the Pareto plot PDF. Default: <hopt-dir>/results."),
    )
    parser.add_argument(
        "--highlight-mpc-best",
        action="store_true",
        help="Highlight the best ranked MPC trial from the hopt study.",
    )
    args = parser.parse_args()

    # Discover paired studies
    paired = find_paired_studies(args.hopt_dir)
    if not paired:
        raise SystemExit(
            f"\nNo paired MPC↔RBC studies found under {args.hopt_dir}. "
            f"Expected study names matching 'mpc_tuning_<id>' and 'rbc_tuning_<id>'."
        )
    p = paired[0]
    print(f"🔍  Paired studies (run_id={p.run_id}):")
    print(f"   MPC study : {p.mpc_study}  (db: {p.mpc_db})")
    print(f"   RBC study : {p.rbc_study}  (db: {p.rbc_db})")

    # ── highlight trial (optional) ────────────────────────────────
    highlight = None
    if args.highlight_mpc_best:
        ranked = get_sorted_best_trials(
            study_name=p.mpc_study,
            db_path=p.mpc_db,
            weights=[3, 20],
        )
        if ranked:
            rt = ranked[0]
            # Need to re-load the study to read raw values (ranking flips axes)
            _study = optuna.load_study(
                study_name=p.mpc_study,
                storage=f"sqlite:///{p.mpc_db}",
            )
            _trial = next(t for t in _study.trials if t.number == rt.trial.number)
            highlight = {
                "x": _trial.values[0],
                "y": _trial.values[1],
                "trial_number": _trial.number,
                "rank": rt.rank,
            }
            print(f"   Highlighting MPC trial #{_trial.number} (rank {rt.rank})")

    # ── plot ─────────────────────────────────────────────────────
    pareto_fig = plot_pareto_dominant(
        studies=[
            ParetoStudy(
                db_path=p.mpc_db,
                study_name=p.mpc_study,
                label=MPC_STYLE[0],
                colour=MPC_STYLE[1],
            ),
            ParetoStudy(
                db_path=p.rbc_db,
                study_name=p.rbc_study,
                label=RBC_STYLE[0],
                colour=RBC_STYLE[1],
            ),
        ],
        target_names=("Energy (Wh)", "Comfort violation (K·h)"),
        highlight=highlight,
        ylim=(0, 50),
        xlim=(8e5, 3.5e6),
    )

    # Save
    output_dir = args.output_dir or Path(args.hopt_dir) / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "mpc_pareto_front.pdf"
    pareto_fig.savefig(out_path)
    print(f"📄  Pareto front saved to {out_path}")
    print("Done")


if __name__ == "__main__":
    main()
