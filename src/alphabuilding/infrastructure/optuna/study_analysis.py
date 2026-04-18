from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence

import numpy as np
import optuna
from joblib import Memory
from optuna.study import Study, StudyDirection
from optuna.trial import FrozenTrial

optuna.logging.set_verbosity(optuna.logging.WARNING)


class RankingStrategy(str, Enum):
    UTOPIA = "utopia"  # min Euclidean distance to ideal point (normalised)
    WEIGHTED_SUM = "weighted_sum"  # weighted linear scalarisation (normalised)
    SINGLE_OBJECTIVE = (
        "single_objective"  # sort by one objective, respecting its direction
    )
    TOPSIS = "topsis"  # TOPSIS closeness coefficient


@dataclass(frozen=True)
class RankedTrial:
    """A Pareto-optimal trial with its rank and scalar score (lower = better)."""

    trial: FrozenTrial
    rank: int
    score: float

    @property
    def params(self) -> dict:
        return self.trial.params

    @property
    def values(self) -> tuple[float, ...]:
        return tuple(self.trial.values)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        return (
            f"RankedTrial(rank={self.rank}, score={self.score:.4f}, "
            f"values={self.values}, params={self.params})"
        )


# ── helpers ──────────────────────────────────────────────────────────────────


def _to_minimisation_space(values: np.ndarray, study: Study) -> np.ndarray:
    """
    Flip maximised objectives so the matrix is entirely in minimisation space,
    then normalise each column to [0, 1] where 0 = best, 1 = worst.
    """
    out = values.astype(float).copy()
    for i, direction in enumerate(study.directions):
        if direction == StudyDirection.MAXIMIZE:
            out[:, i] = -out[:, i]

    lo = out.min(axis=0)
    hi = out.max(axis=0)
    span = np.where(hi - lo == 0, 1.0, hi - lo)
    return (out - lo) / span


def _uniform_weights(n: int) -> np.ndarray:
    return np.full(n, 1.0 / n)


def _validate_weights(weights: Sequence[float] | None, n_obj: int) -> np.ndarray:
    if weights is None:
        return _uniform_weights(n_obj)
    w = np.array(weights, dtype=float)
    if len(w) != n_obj:
        raise ValueError(f"Expected {n_obj} weights (one per objective), got {len(w)}.")
    total = w.sum()
    if total == 0:
        raise ValueError("Weights must not all be zero.")
    return w / total  # normalise


# ── scoring functions ─────────────────────────────────────────────────────────


def _score_utopia(normed: np.ndarray) -> np.ndarray:
    """
    Euclidean distance to the utopia point (origin in normalised space).
    Naturally penalises trials that are far from optimal on *any* objective.
    """
    return np.linalg.norm(normed, axis=1)


def _score_weighted_sum(normed: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    Weighted linear scalarisation of normalised objectives.
    Adjust `weights` to encode preference over objectives.
    """
    return normed @ weights


def _score_single_objective(
    values: np.ndarray,
    study: Study,
    objective_idx: int,
) -> np.ndarray:
    """
    Sort purely by one objective, respecting its direction.
    Useful when one objective is a hard constraint and the other is secondary.
    """
    n_obj = len(study.directions)
    if not (0 <= objective_idx < n_obj):
        raise IndexError(
            f"objective_idx={objective_idx} is out of range for a study "
            f"with {n_obj} objectives."
        )
    col = values[:, objective_idx].astype(float)
    if study.directions[objective_idx] == StudyDirection.MAXIMIZE:
        return -col  # invert so lower score = better
    return col


def _score_topsis(normed: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution).

    Returns (1 - closeness_coefficient) so the convention lower = better is kept.
    Best trial: closest to the ideal point AND farthest from the anti-ideal.
    """
    weighted = normed * weights  # (n_trials, n_obj)

    ideal = weighted.min(axis=0)  # best  per objective
    anti_ideal = weighted.max(axis=0)  # worst per objective

    d_pos = np.linalg.norm(weighted - ideal, axis=1)
    d_neg = np.linalg.norm(weighted - anti_ideal, axis=1)

    denom = d_pos + d_neg
    closeness = np.where(denom == 0, 0.0, d_neg / denom)  # ∈ [0, 1], higher = better
    return 1.0 - closeness


# ── public API ────────────────────────────────────────────────────────────────

memory = Memory(location=".cache/joblib", verbose=0)


@memory.cache
def _get_sorted_best_trials_cached(
    study_name: str,
    db_path: Path,
    strategy: RankingStrategy,
    weights: tuple[float, ...] | None,
    objective_idx: int,
    _db_mtime: float,  # cache-bust key — not used in body
) -> list[RankedTrial]:
    """
    Load a multi-objective Optuna study and return its Pareto-optimal trials
    ranked by the chosen strategy (best first, rank 1 = best).

    Parameters
    ----------
    study_name : str
        Name of the study stored in the SQLite database.
    db_path : Path
        Path to the ``*.db`` file.
    strategy : RankingStrategy
        How to rank the Pareto front:
        - ``UTOPIA``         — distance to the ideal point (default, unbiased)
        - ``WEIGHTED_SUM``   — weighted scalarisation; requires ``weights``
        - ``SINGLE_OBJECTIVE`` — sort by one objective; use ``objective_idx``
        - ``TOPSIS``         — TOPSIS closeness coefficient
    weights : sequence of float | None
        Per-objective weights for ``WEIGHTED_SUM`` and ``TOPSIS``.
        Need not be normalised. Defaults to uniform weights.
    objective_idx : int
        Zero-based index of the objective to sort by (``SINGLE_OBJECTIVE`` only).

    Returns
    -------
    list[RankedTrial]
        Pareto-optimal trials, rank 1 first.

    Raises
    ------
    AssertionError
        If ``db_path`` does not exist.
    IndexError
        If ``objective_idx`` is out of range.
    ValueError
        If ``weights`` length mismatches the number of objectives.
    """
    assert db_path.exists(), f"Optuna database not found at {db_path}"

    study = optuna.load_study(
        study_name=study_name,
        storage=f"sqlite:///{db_path}",
    )
    pareto: list[FrozenTrial] = study.best_trials

    if not pareto:
        return []

    values = np.array([t.values for t in pareto])  # (n_trials, n_obj)
    n_obj = len(study.directions)
    w = _validate_weights(weights, n_obj)
    normed = _to_minimisation_space(values, study)

    match strategy:
        case RankingStrategy.UTOPIA:
            scores = _score_utopia(normed)
        case RankingStrategy.WEIGHTED_SUM:
            scores = _score_weighted_sum(normed, w)
        case RankingStrategy.SINGLE_OBJECTIVE:
            scores = _score_single_objective(values, study, objective_idx)
        case RankingStrategy.TOPSIS:
            scores = _score_topsis(normed, w)
        case _:
            raise ValueError(f"Unknown strategy: {strategy!r}")

    order = np.argsort(scores)
    return [
        RankedTrial(trial=pareto[i], rank=rank + 1, score=float(scores[i]))
        for rank, i in enumerate(order)
    ]


def get_sorted_best_trials(
    study_name: str,
    db_path: Path,
    strategy: RankingStrategy = RankingStrategy.UTOPIA,
    weights: Sequence[float] | None = None,
    objective_idx: int = 0,
) -> list[RankedTrial]:
    _db_mtime = db_path.stat().st_mtime
    return _get_sorted_best_trials_cached(
        study_name,
        db_path,
        strategy,
        tuple(weights) if weights is not None else None,  # lists aren't hashable
        objective_idx,
        _db_mtime,
    )


def list_study_names(db_path: Path) -> list[str]:
    """Return all study names present in the given SQLite database."""
    assert db_path.exists(), f"Optuna database not found at {db_path}"
    summaries = optuna.get_all_study_summaries(storage=f"sqlite:///{db_path}")
    return [s.study_name for s in summaries]


# def _reconstruct_array(params: dict, prefix: str) -> np.ndarray:
#     """
#     Gather all params matching ``{prefix}_{i}`` (sorted by index) into an array.
#     Raises KeyError if no matching keys are found.
#     """
#     pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
#     indexed = {int(m.group(1)): v for k, v in params.items() if (m := pattern.match(k))}
#     if not indexed:
#         raise KeyError(f"No params found with prefix '{prefix}_<i>'.")
#     return np.array([indexed[i] for i in sorted(indexed)])


def _reconstruct_array(params: dict, prefix: str, n: int = 5) -> np.ndarray:
    """
    Gather all params matching ``{prefix}_{i}`` (sorted by index) into an array.

    Falls back to a single scalar key ``{prefix}`` and broadcasts it to length
    ``n`` when no indexed keys are found.

    Raises KeyError if neither form is present.
    """
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    indexed = {int(m.group(1)): v for k, v in params.items() if (m := pattern.match(k))}

    if indexed:
        return np.array([indexed[i] for i in sorted(indexed)])

    if prefix in params:
        return np.full(n, params[prefix])

    raise KeyError(
        f"No params found with prefix '{prefix}_<i>' or scalar key '{prefix}'."
    )


def controller_params_from_trial(
    trial: FrozenTrial | RankedTrial,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Reconstruct controller array params from an Optuna trial.

    The study stores params as:
    - ``R_weight_{i}``     (1-indexed)
    - ``slack_weight_{i}`` (1-indexed);
    - ``margin_{i}``       (1-indexed, optional)

    Returns
    -------
    R_weights : np.ndarray
    slack_weights : np.ndarray
    margins : np.ndarray | None
    """
    frozen: FrozenTrial = trial.trial if isinstance(trial, RankedTrial) else trial
    p = frozen.params

    R_weights = _reconstruct_array(p, "R_weight")  # R_weight_1, R_weight_2, …
    slack_weights = _reconstruct_array(
        p, "slack_weight"
    )  # slack_weight_1, slack_weight_2, …
    slack_weights = slack_weights

    margins: np.ndarray | None = None
    if any(k.startswith("margin_") for k in p):
        margins = _reconstruct_array(p, "margin")  # margin_1, margin_2, …

    return R_weights, slack_weights, margins
