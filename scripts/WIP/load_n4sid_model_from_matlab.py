from alphabuilding.application.use_cases.load_n4sid_model import load_matlab_n4sid_model
from alphabuilding.utils.paths import PathsConfig, paths

path_to_matlab_data = paths.data_dir / "matlab" / "optimal_lti_matrices.mat"
assert path_to_matlab_data.exists(), (
    f"MATLAB data file not found: {path_to_matlab_data}"
)
sys_learned, K = load_matlab_n4sid_model(path_to_matlab_data)
