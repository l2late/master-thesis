import pyrootutils

ROOT = pyrootutils.setup_root(
    search_from=__file__,
    indicator=["pyproject.toml", ".git"],
    project_root_env_var=True,
    dotenv=True,
    pythonpath=True,
    cwd=False,  # let Hydra manage cwd
)
