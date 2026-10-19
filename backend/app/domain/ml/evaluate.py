"""How a model is validated (019): split or cross-validation, and every metric of the problem."""

import math
from collections.abc import Iterator
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn import metrics as skm
from sklearn.model_selection import (
    GroupKFold,
    KFold,
    LeaveOneOut,
    RepeatedKFold,
    RepeatedStratifiedKFold,
    StratifiedGroupKFold,
    StratifiedKFold,
)

from app.domain.ml.target import Task
from app.domain.variable.source import clean

Method = Literal["split", "kfold", "repeated_kfold", "group_kfold", "time_split", "loo"]
CROSS = ("kfold", "repeated_kfold", "group_kfold", "loo")
LOO_LIMIT = 1_000

REGRESSION_METRICS = ["r2", "mae", "rmse", "mape", "median_ae", "max_error"]
CLASSIFICATION_METRICS = [
    "accuracy",
    "balanced_accuracy",
    "f1_macro",
    "f1_weighted",
    "precision",
    "recall",
    "roc_auc",
    "pr_auc",
    "log_loss",
    "brier",
    "mcc",
    "kappa",
]
ZERO: Any = 0.0  # zero_division (the stubs expect a string)
LOWER_IS_BETTER = {"mae", "rmse", "mape", "median_ae", "max_error", "log_loss", "brier"}


class Validation(BaseModel):
    """How the model is judged, and on how many rows it is trained."""

    method: Method = "split"
    test_size: float = Field(default=0.2, ge=0.1, le=0.4)
    folds: int = Field(default=5, ge=3, le=10)
    repeats: int = Field(default=3, ge=2, le=10)
    group: str | None = Field(default=None, max_length=500)  # group k-fold
    time_column: str | None = Field(default=None, max_length=500)  # time-based split
    metric: str | None = Field(default=None, max_length=40)  # None: the default for the problem
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    max_rows: int | None = Field(default=200_000, ge=100, le=100_000_000)  # None: every row

    @property
    def cross(self) -> bool:
        return self.method in CROSS


def metrics_for(task: Task) -> list[str]:
    return REGRESSION_METRICS if task == "regression" else CLASSIFICATION_METRICS


def default_metric(task: Task, minority: float | None) -> str:
    if task == "regression":
        return "r2"
    if task == "binary":
        return "roc_auc"
    return "balanced_accuracy" if minority is not None and minority < 0.2 else "accuracy"


class ValidationError(ValueError):
    pass


def check(validation: Validation, task: Task, rows: int, columns: set[str]) -> None:
    if validation.metric is not None and validation.metric not in metrics_for(task):
        raise ValidationError(f"{validation.metric} is not a metric of this problem.")
    if validation.method == "loo" and rows > LOO_LIMIT:
        raise ValidationError(f"Leave-one-out needs ≤ {LOO_LIMIT:,} rows: choose k-fold.")
    if validation.method == "group_kfold" and validation.group not in columns:
        raise ValidationError("Group k-fold needs a group column.")
    if validation.method == "time_split" and validation.time_column not in columns:
        raise ValidationError("A time-based split needs a date column.")


def time_split(when: pd.Series, test_size: float) -> tuple[np.ndarray, np.ndarray]:
    """Test = the most recent rows: no test row is earlier than a training row (rows without a
    date count as the oldest)."""
    if pd.api.types.is_numeric_dtype(when):
        key = when.astype(float).to_numpy()
    else:
        moments = pd.to_datetime(when, errors="coerce")
        key = (moments - moments.min()).dt.total_seconds().to_numpy(dtype=float)
    order = np.argsort(np.nan_to_num(key, nan=-np.inf), kind="stable")
    cut = round(len(order) * (1 - test_size))
    return order[:cut], order[cut:]


def folds(
    validation: Validation, y: pd.Series, groups: pd.Series | None, classification: bool
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Training and held-out positions of every fold."""
    n = len(y)
    stratify = classification and int(y.value_counts().min()) >= validation.folds
    if validation.method == "loo":
        splitter = LeaveOneOut()
    elif validation.method == "group_kfold":
        labels = cast(pd.Series, groups).astype(str).fillna("(empty)").to_numpy()
        k = min(validation.folds, len(set(labels)))
        if k < 2:
            raise ValidationError("Group k-fold needs at least two groups.")
        splitter = (
            StratifiedGroupKFold(k, shuffle=True, random_state=validation.seed)
            if stratify
            else GroupKFold(k)
        )
        yield from splitter.split(np.zeros(n), y.to_numpy(), labels)
        return
    elif validation.method == "repeated_kfold":
        splitter = (
            RepeatedStratifiedKFold(
                n_splits=validation.folds,
                n_repeats=validation.repeats,
                random_state=validation.seed,
            )
            if stratify
            else RepeatedKFold(
                n_splits=validation.folds,
                n_repeats=validation.repeats,
                random_state=validation.seed,
            )
        )
    else:
        splitter = (
            StratifiedKFold(validation.folds, shuffle=True, random_state=validation.seed)
            if stratify
            else KFold(validation.folds, shuffle=True, random_state=validation.seed)
        )
    yield from splitter.split(np.zeros(n), y.to_numpy() if stratify else None)


# --- Metrics --------------------------------------------------------------------------------------


def _safe(compute) -> float | None:
    try:
        value = float(compute())
    except (ValueError, ZeroDivisionError, IndexError):
        return None
    return clean(value) if math.isfinite(value) else None


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | None]:
    positive = bool((actual > 0).all())
    return {
        "r2": _safe(lambda: skm.r2_score(actual, predicted)),
        "mae": _safe(lambda: skm.mean_absolute_error(actual, predicted)),
        "rmse": _safe(lambda: math.sqrt(skm.mean_squared_error(actual, predicted))),
        "mape": _safe(lambda: skm.mean_absolute_percentage_error(actual, predicted) * 100)
        if positive
        else None,
        "median_ae": _safe(lambda: skm.median_absolute_error(actual, predicted)),
        "max_error": _safe(lambda: skm.max_error(actual, predicted)),
    }


def classification_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
    probabilities: np.ndarray,
    classes: list[str],
    positive: str | None,
) -> dict[str, float | None]:
    found: dict[str, float | None] = {
        "accuracy": _safe(lambda: skm.accuracy_score(actual, predicted)),
        "balanced_accuracy": _safe(lambda: skm.balanced_accuracy_score(actual, predicted)),
        "f1_macro": _safe(
            lambda: skm.f1_score(actual, predicted, average="macro", zero_division=ZERO)
        ),
        "f1_weighted": _safe(
            lambda: skm.f1_score(actual, predicted, average="weighted", zero_division=ZERO)
        ),
        "precision": _safe(
            lambda: skm.precision_score(actual, predicted, average="macro", zero_division=ZERO)
        ),
        "recall": _safe(
            lambda: skm.recall_score(actual, predicted, average="macro", zero_division=ZERO)
        ),
        "log_loss": _safe(lambda: skm.log_loss(actual, probabilities, labels=classes)),
        "mcc": _safe(lambda: skm.matthews_corrcoef(actual, predicted)),
        "kappa": _safe(lambda: skm.cohen_kappa_score(actual, predicted)),
        "roc_auc": None,
        "pr_auc": None,
        "brier": None,
    }
    if positive is not None and len(classes) == 2:
        truth = (actual == positive).astype(int)
        scores = probabilities[:, classes.index(positive)]
        if 0 < truth.sum() < len(truth):
            found["roc_auc"] = _safe(lambda: skm.roc_auc_score(truth, scores))
            found["pr_auc"] = _safe(lambda: skm.average_precision_score(truth, scores))
        found["brier"] = _safe(lambda: skm.brier_score_loss(truth, scores))
    elif len(set(actual)) == len(classes):
        found["roc_auc"] = _safe(
            lambda: skm.roc_auc_score(actual, probabilities, multi_class="ovr", labels=classes)
        )
    return found


def summarise(
    per_fold: list[dict[str, float | None]],
) -> tuple[dict[str, float | None], dict[str, float | None]]:
    """Mean and standard deviation of every metric over the folds."""
    keys = per_fold[0].keys() if per_fold else []
    mean: dict[str, float | None] = {}
    spread: dict[str, float | None] = {}
    for key in keys:
        values = [v for fold in per_fold if (v := fold.get(key)) is not None]
        mean[key] = clean(float(np.mean(values))) if values else None
        spread[key] = clean(float(np.std(values, ddof=1))) if len(values) > 1 else None
    return mean, spread
