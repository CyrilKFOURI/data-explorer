"""Automatic data preparation by named rules (docs/features/017-ml-preparation-donnees/spec.md).

Each decision comes from the column's profile (validated type, role, statistics) and the model's
profile (does it need scaling? handle missing values?). Every decision carries the id of the rule
that made it and a sentence with the numbers behind it. The scikit-learn pipeline is built from the
decisions, so everything that learns from data (medians, scales, encodings) is fitted on the
training rows only.
"""

import math
from dataclasses import dataclass, field
from typing import Literal, cast

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    OneHotEncoder,
    OrdinalEncoder,
    PowerTransformer,
    RobustScaler,
    StandardScaler,
    TargetEncoder,
)

from app.domain.ml.data import CATEGORICAL, NUMERIC, Field
from app.domain.ml.target import Task

ONE_HOT_LIMIT = 15
TARGET_ENCODING_LIMIT = 100
INDICATOR_SHARE = 0.05
RARE_SHARE, RARE_ROWS = 0.01, 10
MISSING = "Missing"


@dataclass(frozen=True)
class ModelProfile:
    """What a model needs from its inputs (017 spec, « Profil du modèle »)."""

    needs_scaling: bool = False
    handles_missing: bool = False
    native_categorical: bool = False
    sensitive_to_skew: bool = False
    sensitive_to_collinearity: bool = False
    tree_based: bool = False
    nonnegative_inputs: bool = False


@dataclass
class ColumnProfile:
    name: str
    type: str
    role: str | None
    missing_share: float
    distinct: int
    dominant_share: float  # share of the most frequent value
    skewness: float | None
    outlier_share: float | None  # beyond 1.5 IQR
    all_nonnegative: bool | None
    distinct_share: float  # distinct values / non-missing rows


@dataclass
class Decision:
    column: str
    type: str
    use: bool
    rules: list[str] = field(default_factory=list)  # rule ids, in the order they applied
    why: list[str] = field(default_factory=list)  # one sentence per rule
    impute: str | None = None  # median, mean, most_frequent, missing_category, none
    indicator: bool = False
    transform: str | None = None  # log1p, yeojohnson, date_parts
    encoding: str | None = None  # binary, onehot, target, ordinal
    scaling: str | None = None  # standard, robust
    order: list[str] | None = None  # categories of an ordinal column

    def apply(self, rule: str, sentence: str) -> None:
        self.rules.append(rule)
        self.why.append(sentence)


@dataclass
class Preparation:
    decisions: list[Decision]
    inputs: int = 0  # model inputs once prepared (filled after fitting)
    excluded: int = 0

    @property
    def used(self) -> list[Decision]:
        return [d for d in self.decisions if d.use]


def _col(frame: pd.DataFrame, name: str) -> pd.Series:
    """One column of the frame, typed as a series."""
    return cast(pd.Series, frame[name])


# --- Profiles ------------------------------------------------------------------------------------


def profile(series: pd.Series, fld: Field) -> ColumnProfile:
    n = len(series)
    present = series.dropna()
    missing = 1 - len(present) / n if n else 0.0
    counts = present.astype(str).value_counts() if len(present) else pd.Series(dtype=int)
    distinct = int(counts.size)
    dominant = float(counts.iloc[0] / len(present)) if distinct else 1.0
    skewness = outliers = nonnegative = None
    if fld.type in NUMERIC and len(present) > 2:
        values = present.to_numpy(dtype=float)
        if np.ptp(values) > 0:
            skewness = float(stats.skew(values))
        q1, q3 = np.percentile(values, [25, 75])
        iqr = q3 - q1
        outliers = (
            float(np.mean((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)))
            if iqr > 0
            else 0.0
        )
        nonnegative = bool(values.min() >= 0)
    return ColumnProfile(
        fld.name,
        fld.type,
        fld.role,
        missing,
        distinct,
        dominant,
        skewness,
        outliers,
        nonnegative,
        distinct / len(present) if len(present) else 0.0,
    )


def _association(
    feature: pd.Series, target: pd.Series, feature_numeric: bool, target_numeric: bool
) -> float:
    """|r| (numbers), Cramér's V (categories) or the correlation ratio η (mixed)."""
    pair = pd.DataFrame({"x": feature, "y": target}).dropna()
    if len(pair) < 10:
        return 0.0
    if feature_numeric and target_numeric:
        if pair["x"].std() == 0 or pair["y"].std() == 0:
            return 0.0
        return abs(float(np.corrcoef(pair["x"], pair["y"])[0, 1]))
    if not feature_numeric and not target_numeric:
        table = pd.crosstab(pair["x"].astype(str), pair["y"].astype(str))
        if min(table.shape) < 2:
            return 0.0
        chi2 = float(np.asarray(stats.chi2_contingency(table, correction=False)[0], dtype=float))
        return float(math.sqrt(chi2 / (len(pair) * (min(table.shape) - 1))))
    numbers, groups = (pair["x"], pair["y"]) if feature_numeric else (pair["y"], pair["x"])
    total = float(((numbers - numbers.mean()) ** 2).sum())
    if total == 0:
        return 0.0
    grouped = numbers.groupby(groups.astype(str)).agg(["count", "mean"])
    between = float((grouped["count"] * (grouped["mean"] - numbers.mean()) ** 2).sum())
    return math.sqrt(between / total)


def _separation(feature: pd.Series, target: pd.Series) -> float:
    """How well a single threshold on a number separates two classes (AUC, either direction)."""
    pair = pd.DataFrame({"x": feature, "y": target.astype(str)}).dropna()
    if len(pair) < 10 or pair["y"].nunique() != 2 or pair["x"].nunique() < 2:
        return 0.0
    positive = pair["y"] == pair["y"].iloc[0]
    ranks = stats.rankdata(pair["x"])
    n_pos, n_neg = int(positive.sum()), int((~positive).sum())
    auc = (ranks[positive.to_numpy()].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    return float(max(auc, 1 - auc))


# --- Rules ---------------------------------------------------------------------------------------


def decide(
    frame: pd.DataFrame,
    fields: list[Field],
    target: Field,
    task: Task,
    model: ModelProfile,
    excluded_columns: set[str] | None = None,
) -> Preparation:
    """One decision per column, from the rules of the 017 spec."""
    decisions = []
    excluded_columns = excluded_columns or set()
    target_numeric = task == "regression"
    for fld in fields:
        decision = Decision(fld.name, fld.type, True)
        decisions.append(decision)
        if fld.name == target.name:
            decision.use = False
            decision.apply("R-SEL-01", "This is the target.")
            continue
        if fld.name in excluded_columns:
            decision.use = False
            decision.apply("R-SEL-08", "Ignored in the Columns page.")
            continue
        prof = profile(_col(frame, fld.name), fld)
        if fld.type == "identifier" or (
            fld.type in CATEGORICAL
            and (
                (prof.distinct_share > 0.5 and prof.distinct > 20)
                or prof.distinct > TARGET_ENCODING_LIMIT
            )
        ):
            decision.use = False
            decision.apply(
                "R-SEL-02", f"Behaves like an identifier ({prof.distinct:,} distinct values)."
            )
            continue
        if fld.type == "text":
            decision.use = False
            decision.apply("R-SEL-03", "Free text is left out (text features come later).")
            continue
        if prof.distinct <= 1 or prof.dominant_share > 0.99:
            decision.use = False
            decision.apply("R-SEL-04", f"Almost always the same value ({prof.dominant_share:.1%}).")
            continue
        if prof.missing_share > 0.8:
            decision.use = False
            decision.apply("R-SEL-05", f"{prof.missing_share:.0%} empty.")
            continue
        if fld.type in NUMERIC | CATEGORICAL:
            strength = _association(
                _col(frame, fld.name), _col(frame, target.name), fld.type in NUMERIC, target_numeric
            )
            if strength >= 0.98:
                decision.use = False
                decision.apply(
                    "R-SEL-06",
                    "Looks like it contains the answer "
                    f"(association {strength:.3f} with the target).",
                )
                continue
            separation = (
                _separation(_col(frame, fld.name), _col(frame, target.name))
                if task == "binary" and fld.type in NUMERIC
                else 0.0
            )
            if separation >= 0.995:
                decision.use = False
                decision.apply(
                    "R-SEL-06",
                    "Looks like it contains the answer: one threshold separates the classes "
                    f"(AUC {separation:.3f}).",
                )
                continue
        if fld.type in NUMERIC:
            _numeric(decision, prof, model)
        elif fld.type == "boolean":
            _boolean(decision, prof, model)
        elif fld.type == "categorical_ordinal":
            _ordinal(decision, fld, prof, model)
        elif fld.type == "categorical_nominal":
            _nominal(decision, prof, model)
        elif fld.type == "datetime":
            _date(decision, model)
        else:
            decision.use = False
            decision.apply("R-SEL-03", "This type is not used by models yet.")
    if model.sensitive_to_collinearity:
        _collinearity(frame, decisions, target, target_numeric)
    return Preparation(
        decisions, excluded=sum(not d.use for d in decisions if d.column != target.name)
    )


def _numeric(decision: Decision, prof: ColumnProfile, model: ModelProfile) -> None:
    if model.handles_missing:
        decision.impute = "none"
        decision.apply("R-NUM-01", "Missing values are handled natively by the model.")
    elif prof.skewness is not None and abs(prof.skewness) <= 0.5:
        decision.impute = "mean"
        decision.apply(
            "R-NUM-02", f"Missing values → mean (nearly symmetric, skewness {prof.skewness:.2f})."
        )
    else:
        decision.impute = "median"
        skew = "unknown" if prof.skewness is None else f"{prof.skewness:.2f}"
        decision.apply("R-NUM-03", f"Missing values → median (skewness {skew}).")
    if prof.missing_share > INDICATOR_SHARE and not model.handles_missing:
        decision.indicator = True
        decision.apply(
            "R-NUM-04",
            f"Adds a “was missing” indicator ({prof.missing_share:.0%} empty: often informative).",
        )
    if model.tree_based:
        decision.apply(
            "R-NUM-10", "Trees are unaffected by monotonic transformations and scales: kept as is."
        )
        return
    if model.sensitive_to_skew and prof.skewness is not None and abs(prof.skewness) > 1:
        if prof.all_nonnegative and prof.skewness > 1:
            decision.transform = "log1p"
            decision.apply(
                "R-NUM-05", f"log1p: skewness {prof.skewness:.2f} > 1 and every value ≥ 0."
            )
        else:
            decision.transform = "yeojohnson"
            decision.apply(
                "R-NUM-06",
                f"Yeo-Johnson: |skewness| {abs(prof.skewness):.2f} > 1 with negative values.",
            )
    if model.needs_scaling:
        if prof.outlier_share is not None and prof.outlier_share > 0.05:
            decision.scaling = "robust"
            decision.apply(
                "R-NUM-07",
                f"Robust scaling (median, IQR): {prof.outlier_share:.0%} of values are outliers.",
            )
        else:
            decision.scaling = "standard"
            decision.apply("R-NUM-08", "Standardised (mean 0, standard deviation 1).")


def _boolean(decision: Decision, prof: ColumnProfile, model: ModelProfile) -> None:
    decision.encoding = "binary"
    decision.apply("R-BOOL-01", "Encoded 0 / 1.")
    if prof.missing_share > INDICATOR_SHARE and not model.handles_missing:
        decision.impute = "missing_category"
        decision.apply(
            "R-BOOL-02", f"Missing values are their own category ({prof.missing_share:.0%} empty)."
        )
    else:
        decision.impute = "most_frequent"
        decision.apply("R-BOOL-02", "The few missing values take the most frequent value.")


def _ordinal(decision: Decision, fld: Field, prof: ColumnProfile, model: ModelProfile) -> None:
    if not fld.order:
        decision.apply("R-ORD-02", "No order set in Columns: treated as unordered categories.")
        _nominal(decision, prof, model)
        return
    decision.impute = "most_frequent"
    decision.encoding = "ordinal"
    decision.order = list(fld.order)
    decision.apply(
        "R-ORD-01",
        "Encoded 0 to k-1 in the order validated in Columns: "
        + " < ".join(fld.order[:6])
        + ("…" if len(fld.order) > 6 else ""),
    )
    if model.needs_scaling:
        decision.scaling = "standard"
        decision.apply("R-NUM-08", "Standardised like a number.")


def _nominal(decision: Decision, prof: ColumnProfile, model: ModelProfile) -> None:
    decision.impute = "missing_category"
    decision.apply(
        "R-CAT-01",
        f"Missing values become “{MISSING}”; "
        "categories under 1 % (and 10 rows) are grouped as Other.",
    )
    if prof.distinct == 2:
        decision.encoding = "binary"
        decision.apply("R-CAT-02", "Two categories: one 0 / 1 column.")
    elif model.native_categorical:
        decision.encoding = "native"
        decision.apply("R-CAT-03", "Passed as a category: the model handles categories natively.")
    elif model.tree_based:
        decision.encoding = "ordinal" if prof.distinct <= 50 else "target"
        decision.apply(
            "R-CAT-04",
            "Ordinal codes for trees."
            if prof.distinct <= 50
            else "Target encoding (more than 50 categories).",
        )
    elif prof.distinct <= ONE_HOT_LIMIT or model.nonnegative_inputs:
        decision.encoding = "onehot"
        rule = (
            "R-CAT-07" if model.nonnegative_inputs and prof.distinct > ONE_HOT_LIMIT else "R-CAT-05"
        )
        decision.apply(rule, f"One-hot: {prof.distinct} categories.")
    else:
        decision.encoding = "target"
        decision.apply(
            "R-CAT-06",
            f"Target encoding, cross-fitted on 5 folds ({prof.distinct} categories: "
            "one-hot would add too many columns).",
        )


def _date(decision: Decision, model: ModelProfile) -> None:
    decision.transform = "date_parts"
    decision.impute = "median"
    decision.apply(
        "R-DATE-01",
        "Replaced by its parts (year, month, day, weekday, weekend, hour) "
        "and days since the start.",
    )
    if not model.tree_based:
        decision.apply(
            "R-DATE-03", "Month, weekday and hour as sine / cosine (December is next to January)."
        )
        if model.needs_scaling:
            decision.scaling = "standard"
    else:
        decision.apply("R-DATE-02", "Parts as integers for trees.")


def _collinearity(
    frame: pd.DataFrame, decisions: list[Decision], target: Field, target_numeric: bool
) -> None:
    """R-SEL-07: of two numbers with |r| > 0.95, drop the one less linked to the target."""
    numeric = [d for d in decisions if d.use and d.type in NUMERIC]
    for i, first in enumerate(numeric):
        for second in numeric[i + 1 :]:
            if not (first.use and second.use):
                continue
            pair = frame[[first.column, second.column]].dropna()
            if len(pair) < 10 or float(np.min(np.asarray(pair.std(), dtype=float))) == 0:
                continue
            r = abs(float(np.corrcoef(pair[first.column], pair[second.column])[0, 1]))
            if r <= 0.95:
                continue
            link = {
                d.column: _association(
                    _col(frame, d.column), _col(frame, target.name), True, target_numeric
                )
                for d in (first, second)
            }
            drop, keep = (
                (first, second) if link[first.column] < link[second.column] else (second, first)
            )
            drop.use = False
            drop.apply(
                "R-SEL-07",
                f"Nearly duplicates {keep.column} (r = {r:.3f}); unstable coefficients otherwise.",
            )


# --- Pipeline ------------------------------------------------------------------------------------


class DateParts(BaseEstimator, TransformerMixin):
    """Date → year, month, day, weekday, weekend, hour (when they vary) and days since the start."""

    def __init__(self, cyclical: bool = True) -> None:
        self.cyclical = cyclical

    def fit(self, X, y=None):
        values = pd.to_datetime(pd.Series(np.asarray(X).ravel()))
        self.start_ = values.min()
        self.hour_ = bool(values.dt.hour.nunique() > 1)
        self.names_ = self._names()
        return self

    def _names(self) -> list[str]:
        names = ["year", "day", "weekend", "days_since_start"]
        cycles = ["month", "weekday"] + (["hour"] if self.hour_ else [])
        if self.cyclical:
            names += [f"{c}_{f}" for c in cycles for f in ("sin", "cos")]
        else:
            names += cycles
        return names

    def transform(self, X):
        values = pd.to_datetime(pd.Series(np.asarray(X).ravel()))
        out = {
            "year": values.dt.year,
            "day": values.dt.day,
            "weekend": (values.dt.weekday >= 5).astype(float),
            "days_since_start": (values - self.start_).dt.total_seconds() / 86_400,
        }
        cycles = {"month": (values.dt.month - 1, 12), "weekday": (values.dt.weekday, 7)}
        if self.hour_:
            cycles["hour"] = (values.dt.hour, 24)
        for name, (value, period) in cycles.items():
            if self.cyclical:
                out[f"{name}_sin"] = np.sin(2 * np.pi * value / period)
                out[f"{name}_cos"] = np.cos(2 * np.pi * value / period)
            else:
                out[name] = value
        return pd.DataFrame(out)[self.names_].to_numpy(dtype=float)

    def get_feature_names_out(self, input_features=None):
        prefix = input_features[0] if input_features is not None and len(input_features) else "date"
        return np.array([f"{prefix}_{name}" for name in self.names_], dtype=object)


def _scaler(kind: str | None):
    return {"standard": StandardScaler(), "robust": RobustScaler()}.get(kind or "", "passthrough")


def _rare(n: int) -> int:
    return max(RARE_ROWS, math.ceil(RARE_SHARE * n))


def build(
    preparation: Preparation, rows: int, task: Task, drop_first: bool = False
) -> ColumnTransformer:
    """The scikit-learn ColumnTransformer that applies the decisions."""
    transformers = []
    for d in preparation.used:
        steps: list[tuple[str, object]] = []
        if d.type in NUMERIC:
            if d.impute in ("mean", "median"):
                steps.append(
                    ("impute", SimpleImputer(strategy=d.impute, add_indicator=d.indicator))
                )
            if d.transform == "log1p":
                steps.append(
                    ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one"))
                )
            elif d.transform == "yeojohnson":
                steps.append(
                    ("yeojohnson", PowerTransformer(method="yeo-johnson", standardize=False))
                )
            steps.append(("scale", _scaler(d.scaling)))
        elif d.type == "datetime":
            steps += [
                ("parts", DateParts(cyclical="R-DATE-03" in d.rules)),
                ("impute", SimpleImputer(strategy="median")),
                ("scale", _scaler(d.scaling)),
            ]
        else:
            fill = MISSING if d.impute == "missing_category" else None
            steps.append(
                (
                    "impute",
                    SimpleImputer(strategy="constant", fill_value=fill)
                    if fill
                    else SimpleImputer(strategy="most_frequent"),
                )
            )
            if d.encoding == "ordinal" and d.order:
                steps.append(
                    (
                        "ordinal",
                        OrdinalEncoder(
                            categories=[d.order],  # type: ignore[arg-type]
                            handle_unknown="use_encoded_value",
                            unknown_value=-1,
                        ),
                    )
                )
                steps.append(("scale", _scaler(d.scaling)))
            elif d.encoding == "ordinal":
                steps.append(
                    (
                        "ordinal",
                        OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                    )
                )
            elif d.encoding == "target":
                target_type = (
                    "continuous"
                    if task == "regression"
                    else ("binary" if task == "binary" else "multiclass")
                )
                steps.append(
                    (
                        "target",
                        TargetEncoder(target_type=target_type, smooth=10.0, cv=5, random_state=42),  # type: ignore[arg-type]
                    )
                )
                steps.append(("scale", StandardScaler()))
            else:  # binary, onehot
                steps.append(
                    (
                        "onehot",
                        OneHotEncoder(
                            drop="if_binary"
                            if d.encoding == "binary"
                            else ("first" if drop_first else None),
                            handle_unknown="infrequent_if_exist"
                            if d.encoding == "onehot"
                            else "ignore",
                            min_frequency=_rare(rows) if d.encoding == "onehot" else None,
                            sparse_output=False,
                        ),
                    )
                )
        transformers.append((d.column, Pipeline(steps), [d.column]))
    return ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=False)


Kind = Literal["number", "category", "date"]
