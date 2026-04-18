if __name__ == "__main__":
    from alphabuilding.infrastructure.optuna.study_analysis import (
        RankedTrial,
        RankingStrategy,
        get_sorted_best_trials,
        list_study_names,
    )
    from alphabuilding.utils.paths import paths

    optuna_db_path = paths.log_dir / "mpc_hopt" / "margins" / "optuna_studies.db"
    assert optuna_db_path.exists(), f"Optuna database not found at {optuna_db_path}"

    # Discover available study names
    print(list_study_names(optuna_db_path))
    study_name = "mpc_tuning_with_margins_tighter"

    # Unbiased: closest to the ideal point
    ranked = get_sorted_best_trials(study_name=study_name, db_path=optuna_db_path)

    # ranked = get_sorted_best_trials(
    #     study_name=study_name,
    #     db_path=optuna_db_path,
    #     strategy=RankingStrategy.WEIGHTED_SUM,
    #     weights=[0.75, 0.25],
    # )
    #
    # # Sort purely by comfort violation (obj index 1)
    # ranked = get_sorted_best_trials(
    #     study_name=study_name,
    #     db_path=optuna_db_path,
    #     strategy=RankingStrategy.SINGLE_OBJECTIVE,
    #     objective_idx=1,
    # )

    # Inspect results
    for t in ranked[:5]:
        print(t)
        print(t.params, t.values)
