# AGENTS.md - Guidelines for Agentic Coding Agents

This file provides essential information for AI agents operating in this repository. It covers build/test/lint commands, code style guidelines, and project conventions.

## 🔧 Development Commands

### Testing
- Run all tests: `pytest`
- Run tests with verbose output: `pytest -v`
- Run a single test file: `pytest tests/unit/test_controllers.py`
- Run a single test function: `pytest tests/unit/test_controllers.py::test_rbc_simulation_results`
- Run tests with coverage: `pytest --cov=src`
- Run tests matching a pattern: `pytest -k "test_rbc"`

### Linting & Formatting
- Check linting issues: `ruff check .`
- Fix linting issues automatically: `ruff check --fix .`
- Format code (if formatter configured): `ruff format .`
- Check formatting: `ruff format --check .`

### Type Checking
- Run type checker: `pyright`
- Watch for type errors: `pyright --watch`

### Dependency Management
- Install dependencies: `uv sync`
- Install development dependencies: `uv sync --group dev`
- Update dependencies: `uv lock --update-package <package-name>`

### Running Applications
- Run simulation scripts: `python -m src.alphabuilding.control.simulation`
- Launch JupyterLab: `jupyter lab`
- Run Optuna dashboard: `optuna-dashboard`

## 📝 Code Style Guidelines

### Import Organization
1. Standard library imports first (alphabetized)
2. Third-party imports (alphabetized)
3. Local/application imports (alphabetized)
4. Use absolute imports from project root: `from alphabuilding.control.controllers import RbcController`
5. Never use relative imports (`from .. import module`)
6. Group imports with blank lines between categories

Example:
```python
# Standard library
import itertools
from pathlib import Path
from typing import Literal, Protocol

# Third-party
import control as ct
import jaxtyping
import numpy as np
import scipy.signal

# Local
from alphabuilding.utils.paths import paths
```

### Type Annotations
- Use `jaxtyping` for array/tensor shape annotations: `jaxtyping.Float[np.ndarray, "time actuators"]`
- Prefer explicit type hints over comments
- Use `dataclass(frozen=True)` for immutable data structures
- Use `Protocol` for structural typing/interfaces
- Use `Literal` for finite value sets: `Literal["seconds", "hours"]`
- Avoid `Any` type; if necessary, import and use explicitly: `from typing import Any`

### Naming Conventions
- Classes: `PascalCase` (e.g., `TimedStateSpace`, `ControllerOutput`)
- Functions/variables: `snake_case` (e.g., `get_action`, `simulation_config`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `N_ROOMS`, `U_MAX`)
- Enum values: `UPPER_SNAKE_CASE` (e.g., `SimulationPhase.WARMUP`)
- Private methods/variables: single leading underscore (e.g., `_previous_action`)
- Protected methods/variables: single leading underscore (same as private in Python)

### Dataclass Usage
- Always use `frozen=True` for immutable dataclasses unless mutation is explicitly needed
- Include docstrings for all dataclasses explaining their purpose
- Use field types with proper annotations
- For complex default values, use `default_factory` if needed

### Error Handling
- Prefer explicit error checking over broad exception catching
- When catching exceptions, be specific: `except ValueError:` not `except Exception:`
- Never use bare `except:` clauses
- Log errors appropriately using logging module (not print statements)
- For utility functions that might fail, consider returning `Union[ResultType, ErrorType]` or raising specific exceptions

### Documentation
- All public classes, functions, and methods must have docstrings
- Use Google-style or NumPy-style docstrings consistently
- Docstrings should include:
  - Brief description of purpose
  - Args section with parameter types and descriptions
  - Returns section with return type and description
  - Raises section for exceptions (if applicable)
  - Examples for complex functions (optional but encouraged)
- Use type hints in function signatures; don't repeat types in docstrings unless adding value

### Specific Patterns Observed in Codebase
- Use `jaxtyping` for numpy array shape annotations throughout
- Wrap LTI systems in `TimedStateSpace` to enforce explicit time units
- Use `dataclass(frozen=True)` for configuration objects
- Use `Protocol` for defining interfaces (e.g., `Controller`)
- Use `Enum` for discrete state values (e.g., `SimulationPhase`)
- Use `itertools.product` for parameter sweeps
- Use `Path` objects for file paths (from `pathlib`)
- Use `np.testing.assert_array_equal` for numpy array assertions in tests

### Testing Conventions
- Test files named `test_*.py` or `*_test.py`
- Use pytest fixtures for setup/teardown (`@pytest.fixture`)
- Test functions named `test_*_descriptive_name`
- Use `np.testing.assert_array_equal` for numpy comparisons
- Use `pd.testing.assert_frame_equal` for DataFrame comparisons
- Group related tests in classes when appropriate
- Use descriptive test names that explain the scenario being tested
- For simulation tests, compare against expected results stored in test data

### Configuration Management
- Use Hydra for configuration management (seen in dependencies)
- Configuration files should be in `conf/` directory
- Override configs via command line: `python script.py parameter=value`
- Use `hydra-core` and `hydra-colorlog` for colored logging

### Version Control
- Write clear, descriptive commit messages
- Format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, perf, test, chore
- Scope: optional, indicates module/component affected
- Example: `feat(control): add MPC controller implementation`
- Never commit `.env` files or sensitive data
- Use `.gitignore` to exclude unnecessary files

### Project Structure
- Source code: `src/alphabuilding/`
- Tests: `tests/` (with unit/ and integration/ subdirectories)
- Configuration: `conf/` (Hydra configs)
- Data: `data/` (input/output data)
- Logs: `logs/` (training logs, wandb logs)
- Scripts: `scripts/` (utility scripts)
- Output: `output/` (simulation results, plots)
- MATLAB: `matlab/` (legacy MATLAB code)

### Important Notes
1. The project uses Python 3.10-3.10 (see pyproject.toml)
2. Type checking is enabled with basedpyright (strict mode)
3. linting is configured with ruff (see pyproject.toml)
4. Testing uses pytest with specific configurations (showlocals, strict markers, etc.)
5. The codebase makes heavy use of numpy arrays with jaxtyping for shape safety
6. Control theory libraries used: `control` and `scipy.signal`
7. Machine learning: PyTorch, Lightning, TorchMetrics
8. Experiment tracking: Weights & Biases (wandb)
9. Configuration: Hydra
10. Optimization: Optuna

## 🔍 LSP & Editor Support
- Language Server: basedpyright (configured in pyproject.toml)
- LSP diagnostics are available for immediate feedback
- Ensure your editor supports LSP for best experience
- Format on save is recommended if using ruff formatter

## 🚫 Common Pitfalls to Avoid
1. Don't suppress type errors with `# type: ignore` or `type: ignore` comments
2. Don't use mutable default arguments in functions (`def func(arg=[]):`)
3. Don't ignore linter warnings without fixing them
4. Don't commit debugging print statements
5. Don't use relative imports that break when running as module
6. Don't modify global state unnecessarily
7. Don't hardcode paths; use Path objects or config management
8. Don't ignore time units; always use TimedStateSpace for LTI systems