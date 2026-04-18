from alphabuilding.analysis.evaluation import evaluate_model_predictions
from alphabuilding.utils.chooser import choose_run_dir
from alphabuilding.utils.paths import paths


def main():
    logs_root = paths.log_dir

    # "multiruns/2026-01-13_10-48-22/datamodule.csv_file=five_room_1_year_Ts_0.25_hysteresis-random_Tmargin_1_real.csv_datamodule.noise_stds=[0_0]_experiment=15_minutes_real_hysteresis_random_discrete_soft_stable_observer_solar_1tomany_model.lambda_reg_eigvals=1/lightning_logs/version_0"

    # dynamically select checkpoint with TUI
    run_dir = choose_run_dir(logs_root, auto_select_last=False)

    evaluate_model_predictions(run_dir)
    print("Done")


if __name__ == "__main__":
    main()
