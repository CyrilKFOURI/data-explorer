"""Generation methods. Each one learns from coded training columns and returns coded synthetic
columns of the same kind (numbers, seconds, level indexes; NaN = empty)."""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from app.domain.synthetic.encode import Coded, Learned
from app.domain.synthetic.plan import Method


class Cancelled(Exception):
    """The user stopped the run."""


@dataclass
class Options:
    rows: int
    seed: int = 42
    smooth: bool = True  # CART: Gaussian noise on numbers, scaled to the leaf's spread
    order: list[str] | None = None  # CART: column order (None = automatic)
    drop_copies: bool = True  # replace synthetic rows identical to a training row


@dataclass
class Edge:
    parent: str
    child: str
    strength: float  # mutual information (Bayesian network) or association (CART order)


@dataclass
class Fitted:
    """What the method found, shown with the run."""

    method: Method
    order: list[str] = field(default_factory=list)  # CART: columns in generation order
    edges: list[Edge] = field(default_factory=list)  # Bayesian network: the Chow-Liu tree
    notes: list[str] = field(default_factory=list)
    dropped: int = 0  # synthetic rows identical to a training row, replaced


StopCheck = Callable[[], bool]


def draw_in_groups(
    groups: np.ndarray, values: np.ndarray, wanted: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """For each wanted group, a random training value from the same group (a real value of the
    same leaf or interval). Unknown groups draw from all values."""
    order = np.argsort(groups, kind="stable")
    sorted_groups, sorted_values = groups[order], values[order]
    unique, starts, counts = np.unique(sorted_groups, return_index=True, return_counts=True)
    position = np.searchsorted(unique, wanted)
    position = np.clip(position, 0, len(unique) - 1)
    known = unique[position] == wanted
    start = np.where(known, starts[position], 0)
    count = np.where(known, counts[position], len(sorted_values))
    picked = start + np.floor(rng.random(len(wanted)) * count).astype(np.int64)
    return sorted_values[np.minimum(picked, len(sorted_values) - 1)]


def marginal(values: np.ndarray, rows: int, rng: np.random.Generator) -> np.ndarray:
    """Real values drawn at random, empty ones included."""
    return values[rng.integers(0, len(values), size=rows)]


def generate(
    method: Method,
    coded: Coded,
    learned: list[Learned],
    options: Options,
    should_stop: StopCheck = lambda: False,
) -> tuple[Coded, Fitted]:
    from app.domain.synthetic.methods import bayes, cart, copula, independent

    runners = {
        "cart": cart.generate,
        "copula": copula.generate,
        "bayes": bayes.generate,
        "independent": independent.generate,
    }
    return runners[method](coded, learned, options, should_stop)
