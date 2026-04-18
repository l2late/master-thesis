import pandas as pd


def validate_multiindex_simulation_result(df: pd.DataFrame) -> None:
    assert df.index.nlevels == 2, (
        "DataFrame must have a MultiIndex with (experiment_id, datetime)."
    )
    # assert the right levels are present
    assert df.index.names == ["experiment_id", "datetime"], (
        f"DataFrame index levels must be ['experiment_id', 'datetime'], got {df.index.names}."
    )
