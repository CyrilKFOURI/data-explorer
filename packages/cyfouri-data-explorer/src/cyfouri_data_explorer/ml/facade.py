"""Machine learning on one target, for the library: the app's ML page as methods.

ml = ds.ml("Survived")
model = ml.train()                 # preparation and model chosen by the app's rules
model.score, model.classification  # held-out results
model.explain()                    # permutation importance, SHAP, partial dependence
model.predict(new_rows)            # a Dataset or a pandas DataFrame
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import duckdb
import numpy as np
import pandas as pd

from cyfouri_data_explorer.filters.model import Condition
from cyfouri_data_explorer.filters.scope import scoped_source, where_for
from cyfouri_data_explorer.ml import classes as binning
from cyfouri_data_explorer.ml import data as ml_data
from cyfouri_data_explorer.ml import evaluate
from cyfouri_data_explorer.ml import explain as explainer
from cyfouri_data_explorer.ml import models as catalogue
from cyfouri_data_explorer.ml import preparation as prep
from cyfouri_data_explorer.ml import train as trainer
from cyfouri_data_explorer.ml import tune as tuner
from cyfouri_data_explorer.ml.catalog import Context
from cyfouri_data_explorer.ml.data import NUMERIC, Field
from cyfouri_data_explorer.ml.engine import Catalogue, MlEngine, MlError, TuneStart

if TYPE_CHECKING:
    from cyfouri_data_explorer.dataset import Dataset


class TrainedModel:
    """A trained model: the app's run (scores, predictions, coefficients, importances…) with its
    fitted pipeline. Every field of the result is an attribute (`model.score`, `model.task`)."""

    def __init__(
        self,
        engine: MlEngine,
        dataset_id: str,
        target: str,
        conditions: list[Condition],
        fields: list[Field],
        trained: trainer.Trained,
    ) -> None:
        self._engine = engine
        self._id = dataset_id
        self.target = target
        self._conditions = conditions
        self._fields = fields
        self.result = trained
        self._explanation: explainer.Explanation | None = None

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        return getattr(self.result, name)

    def __repr__(self) -> str:
        score = f"{self.result.score:.4g}" if self.result.score is not None else "n/a"
        return (
            f"<TrainedModel {self.result.model} -> {self.target!r} ({self.result.task}): "
            f"{self.result.primary} {score}>"
        )

    @property
    def pipeline(self) -> Any:
        """The fitted scikit-learn pipeline (preparation + model)."""
        return self.result.pipeline

    @property
    def inputs(self) -> list[str]:
        return [str(c) for c in self.result.pipeline.feature_names_in_]

    def explain(self) -> explainer.Explanation:
        """Permutation importance, SHAP values, partial dependence and the tree (when there is
        one), on the rows the model was scored on."""
        if self._explanation is None:
            self._explanation = self._engine._explanation(
                self._id, self.result.pipeline, self, self._conditions
            )
        return self._explanation

    def predict(self, data: "Dataset | pd.DataFrame") -> pd.DataFrame:
        """Predictions for new rows, read with the training columns' types. Columns: `predicted`,
        and for a classifier one probability column per class (`p(<class>)`)."""
        from cyfouri_data_explorer.dataset import Dataset, from_pandas

        dataset = data if isinstance(data, Dataset) else from_pandas(data, "predict")
        frame = self._inputs(dataset)
        pipeline = self.result.pipeline
        if self.result.task == "regression":
            return pd.DataFrame({"predicted": np.asarray(pipeline.predict(frame), dtype=float)})
        chances = np.asarray(pipeline.predict_proba(frame), dtype=float)
        labels = [str(c) for c in pipeline.classes_]
        predicted = np.asarray(labels, dtype=object)[chances.argmax(axis=1)]
        found = self.result.classification
        if found and found.threshold is not None and found.positive in labels and len(labels) == 2:
            positive = labels.index(found.positive)
            other = labels[1 - positive]
            predicted = np.where(chances[:, positive] >= found.threshold, found.positive, other)
        out = pd.DataFrame({"predicted": predicted.astype(str)})
        for j, label in enumerate(labels):
            out[f"p({label})"] = chances[:, j]
        return out

    def _inputs(self, dataset: "Dataset") -> pd.DataFrame:
        wanted = set(self.inputs)
        fields = [f for f in self._fields if f.name in wanted]
        absent = sorted(wanted - set(dataset.columns))
        if absent:
            raise MlError(f"Columns missing from the new data: {', '.join(absent)}.")
        source = scoped_source(
            str(dataset.path), where_for(dataset.types, dataset.conditions), numbered=True
        )
        selected = ", ".join(f"{ml_data._expression(f)} AS c{i}" for i, f in enumerate(fields))
        connection = duckdb.connect()
        try:
            frame = connection.execute(
                f"SELECT {selected} FROM {source} ORDER BY file_row_number"
            ).df()
        finally:
            connection.close()
        frame.columns = [f.name for f in fields]
        for field in fields:
            if field.type in NUMERIC:  # as ml_data.load reads them
                frame[field.name] = pd.Series(
                    pd.to_numeric(frame[field.name], errors="coerce"),
                    index=frame.index,
                    dtype=float,
                )
        return cast(pd.DataFrame, frame[self.inputs])


@contextmanager
def _readable() -> Iterator[None]:
    """The engine's own errors (bad settings, validation, tuning) as `MlError`, like the app."""
    try:
        yield
    except (
        trainer.TrainingError,
        catalogue.SettingsError,
        evaluate.ValidationError,
        tuner.TuneError,
    ) as error:
        raise MlError(str(error)) from error


Preparation = prep.Choices | dict[str, Any] | None


def _choices(preparation: Preparation) -> prep.Choices | None:
    """Preparation choices given as the model or as a plain dict (validated the same way)."""
    if preparation is None or isinstance(preparation, prep.Choices):
        return preparation
    try:
        return prep.Choices.model_validate(preparation)
    except ValueError as error:
        raise MlError(f"Invalid preparation: {error}") from None


@dataclass
class Failed:
    """A model of a comparison that could not be trained."""

    model: str
    error: str


class MachineLearning:
    """Models predicting one column of a dataset (`classes`: a number cut into classes;
    `validation`: split, k-fold… and the metric)."""

    def __init__(
        self,
        engine: MlEngine,
        dataset_id: str,
        target: str,
        conditions: list[Condition],
        classes: binning.Classes | dict[str, Any] | None = None,
        validation: evaluate.Validation | dict[str, Any] | None = None,
    ) -> None:
        self._engine = engine
        self._id = dataset_id
        self.target = target
        self._conditions = conditions
        try:
            self.classes = (
                binning.Classes.model_validate(classes) if isinstance(classes, dict) else classes
            )
            self.validation = (
                evaluate.Validation.model_validate(validation)
                if isinstance(validation, dict)
                else validation or evaluate.Validation()
            )
        except ValueError as error:
            raise MlError(f"Invalid classes or validation: {error}") from None

    def _request(self, model: str | None = None) -> tuple[list[Field], Field, str]:
        return self._engine._request(self._id, self.target, model, self._conditions, self.classes)

    def task(self) -> str:
        """regression, binary or multiclass."""
        if self.classes is not None:
            return "binary" if len(self.classes.names) == 2 else "multiclass"
        fields, target, source = self._request()
        return self._engine._load(fields, target, source, self.validation.max_rows)[1]

    def catalogue(self) -> Catalogue:
        """The models for this problem, their settings with defaults for this data, and the
        recommended ones."""
        found = self._engine.targets(self._id, self._conditions)
        usable = [c for c in found.candidates if c.name != self.target and c.task is not None]
        categorical = [c for c in usable if c.type not in NUMERIC]
        context = Context(
            rows=found.rows,
            task=self.task(),  # type: ignore[arg-type]
            features=len(usable),
            categorical_share=len(categorical) / len(usable) if usable else 0.0,
            missing_share=float(np.mean([c.missing_share for c in usable])) if usable else 0.0,
        )
        return self._engine.catalogue(context)

    def preview(
        self,
        model: str | None = None,
        settings: dict[str, Any] | None = None,
        preparation: Preparation = None,
    ) -> trainer.PreparationPreview:
        """The preparation the training would use (per column: selection, imputation, encoding,
        scaling) and the first prepared rows."""
        with _readable():
            return self._engine.preview(
                self._id,
                self.target,
                model,
                settings,
                self._conditions,
                _choices(preparation),
                self.classes,
            )

    def estimate(
        self,
        model: str | None = None,
        settings: dict[str, Any] | None = None,
        preparation: Preparation = None,
    ) -> trainer.Estimate:
        """How long the training would take."""
        with _readable():
            return self._engine.estimate(
                self._id,
                self.target,
                model,
                settings,
                self._conditions,
                _choices(preparation),
                self.classes,
                self.validation,
            )

    def train(
        self,
        model: str | None = None,
        settings: dict[str, Any] | None = None,
        preparation: Preparation = None,
    ) -> TrainedModel:
        """Train a model (by default the app's first model for the problem: linear or
        logistic) with the automatic, explained preparation."""
        fields, target, source = self._request(model)
        with _readable():
            trained = self._engine._fit(
                fields,
                target,
                source,
                model,
                settings,
                _choices(preparation),
                self.classes,
                self.validation,
            )
        return TrainedModel(self._engine, self._id, self.target, self._conditions, fields, trained)

    def compare(
        self,
        models: list[str] | None = None,
        preparation: Preparation = None,
        progress: Callable[[str], None] | None = None,
        settings: dict[str, dict[str, Any]] | None = None,
    ) -> list[TrainedModel | Failed]:
        """Train several models with the same validation, seed and preparation (by default one
        per suitable family); best first, failures last. `settings`: per model key, e.g.
        `{"random_forest": {"n_estimators": 500}}`."""
        keys = models or self.catalogue().compare
        unknown = [k for k in keys if k not in catalogue.CATALOGUE]
        if unknown:
            raise MlError(f"Unknown model(s): {', '.join(unknown)}.", "unknown_model")
        found: list[TrainedModel | Failed] = []
        for key in dict.fromkeys(keys):
            if progress is not None:
                progress(key)
            try:
                found.append(self.train(key, (settings or {}).get(key), preparation))
            except MlError as error:
                found.append(Failed(key, str(error)))
        trained = [m for m in found if isinstance(m, TrainedModel)]
        lower = bool(trained) and trained[0].result.primary in evaluate.LOWER_IS_BETTER
        trained.sort(
            key=lambda m: (m.result.score is None, (m.result.score or 0) * (1 if lower else -1))
        )
        return [*trained, *(m for m in found if isinstance(m, Failed))]

    def tune(
        self,
        model: str,
        budget_seconds: int | None = 60,
        trials: int | None = None,
        sampler: tuner.Sampler = "tpe",
        settings: dict[str, Any] | None = None,
        preparation: Preparation = None,
        pruner: tuner.Pruner = "median",
        space: list[tuner.SearchParam | dict[str, Any]] | None = None,
    ) -> tuner.TuneProgress:
        """Search the model's best settings with Optuna on the training rows (best value, best
        settings, every trial, importance of each setting). `settings` stay fixed; `space`
        replaces the searched settings, e.g. `[{"key": "max_depth", "kind": "int", "low": 2,
        "high": 12}]` (the catalogue's space by default: `default_space(model)`)."""
        try:
            searched = (
                None
                if space is None
                else [
                    tuner.SearchParam.model_validate(p) if isinstance(p, dict) else p for p in space
                ]
            )
            request = TuneStart(
                model=model,
                budget_seconds=budget_seconds,
                trials=trials,
                sampler=sampler,
                pruner=pruner,
                space=searched,
                settings=settings or {},
                preparation=_choices(preparation),
            )
        except ValueError as error:
            raise MlError(f"Invalid search: {error}") from None
        fields, target, source = self._request(model)
        spec = catalogue.CATALOGUE[model]
        if not spec.installed:
            raise MlError(f"{spec.label} is not installed: pip install cyfouri-data-explorer[ml].")
        with _readable():
            return self._engine._search(
                fields,
                target,
                source,
                request,
                request.space if request.space is not None else tuner.default_space(spec.key),
                self.classes,
                self.validation,
                lambda: False,
            )
