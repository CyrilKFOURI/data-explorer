"""Train a model on a frame: split, prepare (fitted on training rows only), fit, evaluate."""

import math
import time
import warnings
from dataclasses import dataclass, field
from typing import Any, cast

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn import metrics as skm
from sklearn.calibration import calibration_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

from app.domain.ml import models as catalogue
from app.domain.ml import preparation as prep
from app.domain.ml.data import NUMERIC, Field
from app.domain.ml.target import MAX_CLASSES, Task
from app.domain.variable.source import clean

SEED = 42
TEST_SHARE = 0.2
POINTS = 2_000  # predicted-vs-actual points drawn
PROBABILITIES = 5_000  # test probabilities sent for the threshold slider
PREDICTION_ROWS = 500
OTHER = "Other"
MAX_VIF_FEATURES = 60


@dataclass
class Coefficient:
    feature: str
    estimate: float
    std_error: float | None = None
    low: float | None = None
    high: float | None = None
    p_value: float | None = None
    vif: float | None = None
    per_unit: float | None = None  # in the column's own unit (standardised numbers only)
    odds_ratio: float | None = None  # logistic regression


@dataclass
class ClassReport:
    label: str
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class Curve:
    x: list[float]
    y: list[float]
    thresholds: list[float] = field(default_factory=list)


@dataclass
class RegressionResult:
    r2: float | None
    mae: float | None
    rmse: float | None
    mape: float | None
    baseline_mae: float | None  # always predicting the training mean
    baseline_rmse: float | None
    skill: float | None  # 1 - MAE / baseline MAE
    actual: list[float]
    predicted: list[float]
    residual_bins: list[dict[str, float]]
    heteroscedasticity_p: float | None = None  # Breusch-Pagan on the training residuals


@dataclass
class ClassificationResult:
    labels: list[str]
    positive: str | None  # binary: the class whose probability is shown (the rarer one)
    accuracy: float | None
    balanced_accuracy: float | None
    f1_macro: float | None
    roc_auc: float | None
    log_loss: float | None
    baseline_accuracy: float | None  # always the majority class
    majority: str
    confusion: list[list[int]]  # [actual][predicted], in `labels` order
    report: list[ClassReport]
    roc: Curve | None = None
    pr: Curve | None = None
    calibration: Curve | None = None
    truth: list[int] = field(default_factory=list)  # binary: 1 = positive (sample)
    probability: list[float] = field(default_factory=list)


@dataclass
class PredictionRow:
    row: int
    actual: str
    predicted: str
    error: float | None = None  # regression
    probability: float | None = None  # classification: probability of the predicted class
    correct: bool | None = None


@dataclass
class Trained:
    task: Task
    model: str
    settings: dict[str, Any]
    preparation: prep.Preparation
    train_rows: int
    test_rows: int
    rows: int
    sampled: bool
    seconds: float
    regression: RegressionResult | None
    classification: ClassificationResult | None
    coefficients: list[Coefficient]
    predictions: list[PredictionRow]
    primary: str  # name of the main score
    score: float | None
    pipeline: Any = field(default=None, repr=False)


class TrainingError(ValueError):
    pass


def _quiet(compute):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return compute()


def prepare_target(series: pd.Series, task: Task) -> pd.Series:
    if task == "regression":
        return series.astype(float)
    labels = series.astype(str)
    counts = labels.value_counts()
    if len(counts) > MAX_CLASSES:
        kept = {str(label) for label in list(counts.index)[: MAX_CLASSES - 1]}
        labels = labels.where(labels.isin(kept), OTHER)
    return labels


def _thin(
    curve_x: np.ndarray,
    curve_y: np.ndarray,
    thresholds: np.ndarray | None = None,
    points: int = 200,
) -> Curve:
    index = np.unique(
        np.linspace(0, len(curve_x) - 1, min(points, len(curve_x))).round().astype(int)
    )
    return Curve(
        [float(v) for v in curve_x[index]],
        [float(v) for v in curve_y[index]],
        []
        if thresholds is None
        else [clean(v) or 0.0 for v in thresholds[np.minimum(index, len(thresholds) - 1)]],
    )


def train(
    frame: pd.DataFrame,
    fields: list[Field],
    target: Field,
    task: Task,
    model_key: str,
    given: dict[str, Any] | None,
    rows: int,
    sampled: bool,
    excluded_columns: set[str] | None = None,
) -> Trained:
    started = time.monotonic()
    spec = catalogue.CATALOGUE[model_key]
    if task not in spec.tasks:
        raise TrainingError(f"{spec.label} does not handle {task} problems.")
    y = prepare_target(cast(pd.Series, frame[target.name]), task)
    if task != "regression" and y.nunique() < 2:
        raise TrainingError("The target has a single class in these rows.")
    minority = float(y.value_counts(normalize=True).min()) if task != "regression" else None
    context = catalogue.Context(len(frame), task, minority)
    values = catalogue.resolve(spec, context, given)
    model_profile = catalogue.profile_for(spec, values)
    preparation = prep.decide(frame, fields, target, task, model_profile, excluded_columns)
    if not preparation.used:
        raise TrainingError("No usable feature: every column was left out (see Preparation).")
    features = [d.column for d in preparation.used]
    stratify = y if task != "regression" and y.value_counts().min() >= 2 else None
    x_train, x_test, y_train, y_test, _, row_test = train_test_split(
        frame[features],
        y,
        frame["__row"],
        test_size=TEST_SHARE,
        random_state=SEED,
        stratify=stratify,
    )
    x_train, x_test = cast(pd.DataFrame, x_train), cast(pd.DataFrame, x_test)
    y_train, y_test = cast(pd.Series, y_train), cast(pd.Series, y_test)
    row_test = cast(pd.Series, row_test)
    if len(x_train) < 10 or len(x_test) < 3:
        raise TrainingError("Too few rows to train and test (at least 15 needed).")
    unregularized = model_key == "linear_regression" and values["regularization"] == "none"
    transformer = prep.build(preparation, len(x_train), task, drop_first=unregularized)
    pipeline = Pipeline([("prepare", transformer), ("model", spec.build(values, context))])
    _quiet(lambda: pipeline.fit(x_train, y_train))
    names = [str(n) for n in pipeline.named_steps["prepare"].get_feature_names_out()]
    preparation.inputs = len(names)

    regression = classification = None
    coefficients: list[Coefficient] = []
    predictions: list[PredictionRow] = []
    rng = np.random.default_rng(SEED)
    if task == "regression":
        predicted = np.asarray(pipeline.predict(x_test), dtype=float)
        actual = y_test.to_numpy(dtype=float)
        regression = _regression_scores(actual, predicted, y_train.to_numpy(dtype=float))
        if model_key == "linear_regression":
            coefficients, regression.heteroscedasticity_p = _linear_coefficients(
                pipeline, x_train, y_train.to_numpy(dtype=float), names, preparation, unregularized
            )
        pick = rng.permutation(len(actual))[:PREDICTION_ROWS]
        predictions = [
            PredictionRow(
                int(row_test.iloc[i]),
                _fmt(float(actual[i])),
                _fmt(float(predicted[i])),
                clean(predicted[i] - actual[i]),
            )
            for i in pick
        ]
        primary, score = "r2", regression.r2
    else:
        classification, predicted_labels, probabilities, classes = _classification_scores(
            pipeline, x_test, y_test, target
        )
        coefficients = (
            _logistic_coefficients(pipeline, names) if model_key == "logistic_regression" else []
        )
        actual_labels = y_test.to_numpy()
        pick = rng.permutation(len(actual_labels))[:PREDICTION_ROWS]
        column = {label: i for i, label in enumerate(classes)}
        predictions = [
            PredictionRow(
                int(row_test.iloc[i]),
                str(actual_labels[i]),
                str(predicted_labels[i]),
                probability=clean(probabilities[i, column[str(predicted_labels[i])]]),
                correct=bool(actual_labels[i] == predicted_labels[i]),
            )
            for i in pick
        ]
        imbalanced = minority is not None and minority < 0.2
        primary = (
            "roc_auc" if task == "binary" else ("balanced_accuracy" if imbalanced else "accuracy")
        )
        score = getattr(classification, primary)
    return Trained(
        task,
        model_key,
        values,
        preparation,
        len(x_train),
        len(x_test),
        rows,
        sampled,
        time.monotonic() - started,
        regression,
        classification,
        coefficients,
        predictions,
        primary,
        score,
        pipeline,
    )


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def _regression_scores(
    actual: np.ndarray, predicted: np.ndarray, train_y: np.ndarray
) -> RegressionResult:
    baseline = np.full_like(actual, train_y.mean())
    mae = float(skm.mean_absolute_error(actual, predicted))
    baseline_mae = float(skm.mean_absolute_error(actual, baseline))
    positive = bool((actual > 0).all())
    residuals = actual - predicted
    counts, edges = np.histogram(residuals, bins=min(30, max(5, len(residuals) // 5)))
    pick = np.random.default_rng(SEED).permutation(len(actual))[:POINTS]
    return RegressionResult(
        clean(skm.r2_score(actual, predicted)),
        clean(mae),
        clean(math.sqrt(skm.mean_squared_error(actual, predicted))),
        clean(skm.mean_absolute_percentage_error(actual, predicted) * 100) if positive else None,
        clean(baseline_mae),
        clean(math.sqrt(skm.mean_squared_error(actual, baseline))),
        clean(1 - mae / baseline_mae) if baseline_mae else None,
        [float(v) for v in actual[pick]],
        [float(v) for v in predicted[pick]],
        [
            {"start": float(edges[i]), "end": float(edges[i + 1]), "count": int(c)}
            for i, c in enumerate(counts)
        ],
    )


def _linear_coefficients(
    pipeline: Pipeline,
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    names: list[str],
    preparation: prep.Preparation,
    unregularized: bool,
) -> tuple[list[Coefficient], float | None]:
    design = np.asarray(pipeline.named_steps["prepare"].transform(x_train), dtype=float)
    model = pipeline.named_steps["model"]
    coefficients = [
        Coefficient(name, float(value))
        for name, value in zip(names, np.ravel(model.coef_), strict=True)
    ]
    per_unit = _unit_scales(pipeline, preparation)
    for coefficient in coefficients:
        if coefficient.feature in per_unit:
            coefficient.per_unit = coefficient.estimate / per_unit[coefficient.feature]
    het_p = None
    if unregularized and design.shape[0] > design.shape[1] + 2:
        exog = sm.add_constant(design, has_constant="add")
        fit = _quiet(lambda: sm.OLS(y_train, exog).fit())
        intervals = np.asarray(fit.conf_int(), dtype=float)
        for i, coefficient in enumerate(coefficients, start=1):
            coefficient.std_error = clean(fit.bse[i])
            coefficient.low, coefficient.high = clean(intervals[i, 0]), clean(intervals[i, 1])
            coefficient.p_value = clean(fit.pvalues[i])
        if len(coefficients) <= MAX_VIF_FEATURES:
            for i, coefficient in enumerate(coefficients, start=1):
                coefficient.vif = clean(_quiet(lambda i=i: variance_inflation_factor(exog, i)))
        het_p = clean(_quiet(lambda: het_breuschpagan(fit.resid, exog)[1]))
    coefficients.sort(key=lambda c: -abs(c.estimate))
    return coefficients, het_p


def _unit_scales(pipeline: Pipeline, preparation: prep.Preparation) -> dict[str, float]:
    """Standardised numbers without transformation: the scale that turns a coefficient back into
    'per unit of the column'."""
    scales = {}
    fitted = pipeline.named_steps["prepare"].named_transformers_
    for decision in preparation.used:
        if (
            decision.type in NUMERIC
            and decision.scaling == "standard"
            and decision.transform is None
        ):
            scaler = fitted[decision.column].named_steps["scale"]
            scale = float(scaler.scale_[0]) if hasattr(scaler, "scale_") else 0.0
            if scale > 0:
                scales[decision.column] = scale
    return scales


def _classification_scores(
    pipeline: Pipeline, x_test: pd.DataFrame, y_test: pd.Series, target: Field
):
    model = pipeline.named_steps["model"]
    classes = [str(c) for c in model.classes_]
    probabilities = np.asarray(pipeline.predict_proba(x_test), dtype=float)
    predicted = np.asarray(model.classes_)[probabilities.argmax(axis=1)].astype(str)
    actual = y_test.to_numpy().astype(str)
    labels = classes
    if target.order:
        rank = {label: i for i, label in enumerate(target.order)}
        labels = sorted(classes, key=lambda c: rank.get(c, len(rank)))
    counts = y_test.value_counts()
    majority = str(counts.index[0])
    report = np.asarray(
        skm.precision_recall_fscore_support(actual, predicted, labels=labels, zero_division=0.0),  # type: ignore[arg-type]
        dtype=float,
    )
    result = ClassificationResult(
        labels,
        None,
        clean(skm.accuracy_score(actual, predicted)),
        clean(skm.balanced_accuracy_score(actual, predicted)),
        clean(skm.f1_score(actual, predicted, average="macro", zero_division=0.0)),  # type: ignore[arg-type]
        None,
        clean(_quiet(lambda: skm.log_loss(actual, probabilities, labels=classes))),
        clean(float(counts.iloc[0] / counts.sum())),
        majority,
        skm.confusion_matrix(actual, predicted, labels=labels).tolist(),
        [
            ClassReport(
                label,
                float(report[0][i]),
                float(report[1][i]),
                float(report[2][i]),
                int(report[3][i]),
            )
            for i, label in enumerate(labels)
        ],
    )
    if len(classes) == 2:
        positive = str(counts.index[-1])  # the rarer class
        column = classes.index(positive)
        truth = (actual == positive).astype(int)
        scores = probabilities[:, column]
        if 0 < truth.sum() < len(truth):
            result.roc_auc = clean(skm.roc_auc_score(truth, scores))
            fpr, tpr, thresholds = skm.roc_curve(truth, scores)
            result.roc = _thin(fpr, tpr, thresholds)
            precision, recall, _ = skm.precision_recall_curve(truth, scores)
            result.pr = _thin(recall[::-1], precision[::-1])
            bins = min(10, max(2, len(truth) // 20))
            observed, expected = calibration_curve(truth, scores, n_bins=bins, strategy="quantile")
            result.calibration = Curve([float(v) for v in expected], [float(v) for v in observed])
        result.positive = positive
        pick = np.random.default_rng(SEED).permutation(len(truth))[:PROBABILITIES]
        result.truth = [int(v) for v in truth[pick]]
        result.probability = [float(v) for v in scores[pick]]
    elif len(set(actual)) == len(classes):
        result.roc_auc = clean(
            _quiet(
                lambda: skm.roc_auc_score(actual, probabilities, multi_class="ovr", labels=classes)
            )
        )
    return result, predicted, probabilities, classes


def _logistic_coefficients(pipeline: Pipeline, names: list[str]) -> list[Coefficient]:
    coef = np.atleast_2d(pipeline.named_steps["model"].coef_)
    if coef.shape[0] == 1:
        found = [
            Coefficient(n, float(v), odds_ratio=clean(math.exp(min(v, 50))))
            for n, v in zip(names, coef[0], strict=True)
        ]
    else:  # multiclass: the largest weight across classes
        strongest = coef[np.abs(coef).argmax(axis=0), np.arange(coef.shape[1])]
        found = [Coefficient(n, float(v)) for n, v in zip(names, strongest, strict=True)]
    found.sort(key=lambda c: -abs(c.estimate))
    return found
