"""The model catalogue: each model declares its tasks, its profile and its settings.

016 ships the reference models (linear and logistic regression); 019 extends this catalogue
with every family. Settings are declared once here and served to the interface.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from sklearn.linear_model import Lasso, LinearRegression, LogisticRegression, Ridge

from app.domain.ml.preparation import ModelProfile
from app.domain.ml.target import Task

Level = Literal["essential", "advanced", "expert"]


@dataclass
class Setting:
    key: str
    label: str
    kind: Literal["select", "number"]
    default: Any
    level: Level = "essential"
    options: list[str] = field(default_factory=list)
    minimum: float | None = None
    maximum: float | None = None
    log: bool = False  # a slider on a log scale
    why: str = ""  # why the default
    shown_when: dict[str, list[str]] | None = None  # hidden unless another setting has one of these


@dataclass
class Context:
    """What defaults may depend on."""

    rows: int
    task: Task
    minority_share: float | None  # classification: share of the rarest class


@dataclass
class ModelSpec:
    key: str
    label: str
    family: str
    description: str
    tasks: tuple[Task, ...]
    profile: ModelProfile
    settings: Callable[[Context], list[Setting]]
    build: Callable[[dict[str, Any], Context], Any]


class SettingsError(ValueError):
    pass


LINEAR = ModelProfile(needs_scaling=True, sensitive_to_skew=True, sensitive_to_collinearity=True)
REGULARIZED = ModelProfile(needs_scaling=True, sensitive_to_skew=True)


def _linear_settings(context: Context) -> list[Setting]:
    return [
        Setting(
            "regularization",
            "Regularization",
            "select",
            "none",
            options=["none", "ridge", "lasso"],
            why="None keeps the coefficients readable, with standard errors and p-values.",
        ),
        Setting(
            "alpha",
            "Strength",
            "number",
            1.0,
            minimum=1e-4,
            maximum=1e4,
            log=True,
            why="1 is a moderate penalty on standardised inputs.",
            shown_when={"regularization": ["ridge", "lasso"]},
        ),
    ]


def _linear_build(values: dict[str, Any], context: Context):
    kind = values["regularization"]
    if kind == "ridge":
        return Ridge(alpha=values["alpha"])
    if kind == "lasso":
        return Lasso(alpha=values["alpha"], max_iter=10_000)
    return LinearRegression()


def _logistic_settings(context: Context) -> list[Setting]:
    imbalanced = context.minority_share is not None and context.minority_share < 0.2
    return [
        Setting(
            "C",
            "Regularization strength C",
            "number",
            1.0,
            minimum=1e-4,
            maximum=1e4,
            log=True,
            why="C = 1 is the usual moderate penalty; lower C = simpler model.",
        ),
        Setting(
            "class_weight",
            "Balance classes",
            "select",
            "balanced" if imbalanced else "none",
            options=["none", "balanced"],
            why=(
                f"The rarest class is {context.minority_share:.0%} of rows: weights balance it."
                if imbalanced and context.minority_share is not None
                else "Classes are balanced enough."
            ),
        ),
    ]


def _logistic_build(values: dict[str, Any], context: Context):
    weight = "balanced" if values["class_weight"] == "balanced" else None
    return LogisticRegression(C=values["C"], class_weight=weight, max_iter=1_000)


CATALOGUE: dict[str, ModelSpec] = {
    "linear_regression": ModelSpec(
        "linear_regression",
        "Linear regression",
        "Linear models",
        "A weighted sum of the features: fast, and every weight can be read.",
        ("regression",),
        LINEAR,
        _linear_settings,
        _linear_build,
    ),
    "logistic_regression": ModelSpec(
        "logistic_regression",
        "Logistic regression",
        "Linear models",
        "A weighted sum of the features turned into a probability: fast and interpretable.",
        ("binary", "multiclass"),
        REGULARIZED,
        _logistic_settings,
        _logistic_build,
    ),
}


def default_model(task: Task) -> str:
    return "linear_regression" if task == "regression" else "logistic_regression"


def profile_for(spec: ModelSpec, values: dict[str, Any]) -> ModelProfile:
    """A regularized linear model is not sensitive to collinearity."""
    if spec.key == "linear_regression" and values.get("regularization", "none") != "none":
        return REGULARIZED
    return spec.profile


def resolve(spec: ModelSpec, context: Context, given: dict[str, Any] | None) -> dict[str, Any]:
    """Settings with their defaults, the given values validated."""
    given = given or {}
    values: dict[str, Any] = {}
    for setting in spec.settings(context):
        value = given.get(setting.key, setting.default)
        if setting.kind == "select":
            if value not in setting.options:
                raise SettingsError(f"{setting.label}: choose one of {', '.join(setting.options)}.")
        else:
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise SettingsError(f"{setting.label} must be a number.") from None
            if (setting.minimum is not None and value < setting.minimum) or (
                setting.maximum is not None and value > setting.maximum
            ):
                raise SettingsError(
                    f"{setting.label} must be between {setting.minimum} and {setting.maximum}."
                )
        values[setting.key] = value
    unknown = set(given) - set(values)
    if unknown:
        raise SettingsError(f"Unknown setting(s): {', '.join(sorted(unknown))}.")
    return values
