"""Rule-based insights: what deserves attention, in one sentence each, with a link to the proof."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import stats

from app.domain.correlations.matrix import ROLES, Loaded, Matrix, MatrixColumn, Pair

SKEWED = 2.0
DOMINANT = 0.7
MISSING = 0.2
STRONG = 0.7
REDUNDANT = 0.95
GROUP_EFFECT = 0.4
ASSOCIATED = 0.3
MAX_INSIGHTS = 30

Kind = Literal[
    "skewed", "imbalanced", "missing", "correlated", "redundant", "group_difference", "associated"
]


@dataclass
class InsightLink:
    page: Literal["variable", "compare"]
    x: str
    y: str | None = None


@dataclass
class Insight:
    id: str  # stable across recomputations, to remember dismissals
    kind: Kind
    severity: Literal["warning", "info"]
    text: str
    columns: list[str]
    link: InsightLink
    score: float  # importance, for sorting


def _pct(share: float) -> str:
    return f"{share * 100:.0f}%"


def _p(p: float | None) -> str:
    if p is None:
        return ""
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def column_insights(
    loaded: Loaded,
    columns: list[MatrixColumn],
    top_shares: dict[str, tuple[str, float]],
) -> list[Insight]:
    """Skewness, missing values and dominant categories, on the rows the matrix was built on."""
    insights: list[Insight] = []
    for c in columns:
        data = loaded.arrays.get(c.name)
        if data is None or not len(data):
            continue
        skew = None
        if ROLES.get(c.type) == "num":
            present_values = data[~np.isnan(data)]
            missing = 1 - len(present_values) / len(data)
            if len(present_values) > 2 and np.ptp(present_values) > 0:
                skew = float(stats.skew(present_values, bias=False))
        else:
            missing = float((data < 0).mean())
        if missing >= MISSING:
            insights.append(
                Insight(
                    f"missing:{c.name}",
                    "missing",
                    "warning",
                    f"{_pct(missing)} of the values of {c.name} are missing.",
                    [c.name],
                    InsightLink("variable", c.name),
                    0.5 + missing,
                )
            )
        if skew is not None and skew == skew and abs(skew) > SKEWED:
            side = "right: a few very large values" if skew > 0 else "left: a few very small values"
            insights.append(
                Insight(
                    f"skewed:{c.name}",
                    "skewed",
                    "info",
                    f"{c.name} is strongly skewed to the {side} (skewness {skew:.1f}). "
                    "Medians describe it better than means; a log transform may help.",
                    [c.name],
                    InsightLink("variable", c.name),
                    0.4 + min(abs(skew), 10) / 20,
                )
            )
        if c.name in top_shares:
            label, share = top_shares[c.name]
            if share > DOMINANT:
                insights.append(
                    Insight(
                        f"imbalanced:{c.name}",
                        "imbalanced",
                        "info",
                        f'{c.name} is imbalanced: "{label}" makes up {_pct(share)} of the rows.',
                        [c.name],
                        InsightLink("variable", c.name),
                        0.3 + share / 2,
                    )
                )
    return insights


def pair_insight(pair: Pair, roles: dict[str, str]) -> Insight | None:
    a, b, value = pair.a, pair.b, pair.value
    link = InsightLink("compare", a, b)
    key = f"{a}|{b}"
    if pair.metric in ("pearson", "spearman"):
        symbol = "r" if pair.metric == "pearson" else "ρ"
        if abs(value) > REDUNDANT:
            return Insight(
                f"redundant:{key}",
                "redundant",
                "warning",
                f"{a} and {b} are almost identical ({symbol} = {value:.3f}): probably redundant, "
                "keep one of them in models.",
                [a, b],
                link,
                2 + abs(value),
            )
        if abs(value) >= STRONG:
            direction = "rises with" if value > 0 else "falls as"
            return Insight(
                f"correlated:{key}",
                "correlated",
                "info",
                f"{b} {direction} {a} ({symbol} = {value:.2f}, {_p(pair.p_value)}).",
                [a, b],
                link,
                1 + abs(value),
            )
        return None
    if pair.metric == "eta" and value >= GROUP_EFFECT:
        numeric, groups = (a, b) if roles.get(a) == "num" else (b, a)
        return Insight(
            f"group_difference:{key}",
            "group_difference",
            "info",
            f"{numeric} differs strongly across the groups of {groups} "
            f"(η = {value:.2f}, {_p(pair.p_value)}).",
            [a, b],
            InsightLink("compare", groups, numeric),
            1 + value,
        )
    if pair.metric == "cramers_v" and value > REDUNDANT:
        return Insight(
            f"redundant:{key}",
            "redundant",
            "warning",
            f"{a} and {b} carry nearly the same information (Cramér's V = {value:.2f}): "
            "one probably determines the other.",
            [a, b],
            link,
            2 + value,
        )
    if pair.metric == "cramers_v" and value >= ASSOCIATED:
        return Insight(
            f"associated:{key}",
            "associated",
            "info",
            f"{a} and {b} are associated (Cramér's V = {value:.2f}, {_p(pair.p_value)}).",
            [a, b],
            link,
            1 + value,
        )
    return None


def top_shares(loaded: Loaded) -> dict[str, tuple[str, float]]:
    """Most frequent category and its share among present values (code 0 = most frequent)."""
    shares: dict[str, tuple[str, float]] = {}
    for name, labels in loaded.labels.items():
        codes = loaded.arrays[name]
        present = codes[codes >= 0]
        if len(present) and labels:
            shares[name] = (labels[0], float((present == 0).mean()))
    return shares


def insights_for(columns: list[MatrixColumn], matrix: Matrix, loaded: Loaded) -> list[Insight]:
    found = column_insights(loaded, columns, top_shares(loaded))
    roles = {column.name: column.role for column in matrix.columns}
    found += [insight for pair in matrix.pairs if (insight := pair_insight(pair, roles))]
    found.sort(key=lambda insight: -insight.score)
    return found[:MAX_INSIGHTS]
