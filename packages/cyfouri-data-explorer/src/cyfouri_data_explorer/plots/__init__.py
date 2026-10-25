"""The app's charts in Python: `dx.plot(result)` draws a result as the app does, as a plotly
figure (the `plot` extra). The figure functions take plain data (`to_dict`) and mirror the
frontend's builders one for one."""

from typing import Any

from cyfouri_data_explorer.errors import ExplorerError
from cyfouri_data_explorer.plots import charts, compare, kpi, ml, synthetic, timeseries, variable
from cyfouri_data_explorer.plots.theme import Theme, Tokens, compose, tokens_for
from cyfouri_data_explorer.results import to_dict

__all__ = ["figure_data", "plot"]

Built = dict[str, Any]


class PlotError(ExplorerError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="plot", status_code=422)


def _rows_height(rows: int, per_row: int = 24) -> int:
    """Height of a chart with one bar per row, never below the app's panels (240 px)."""
    return max(240, 60 + per_row * rows)


def _view(view: str | None, views: list[str], what: str) -> str:
    if view is None:
        return views[0]
    if view not in views:
        raise PlotError(f"{what} has no view {view!r}: choose {', '.join(views)}.")
    return view


def _infer_type(chart: dict[str, Any]) -> str:
    return {"histogram": "numeric_continuous", "timeline": "datetime"}.get(
        chart["kind"], "categorical_nominal"
    )


def _variable(profile: dict[str, Any], view: str | None, tokens: Tokens) -> tuple[Built, int]:
    if profile.get("numeric"):
        numeric = profile["numeric"]
        chosen = _view(view, ["kde", "ecdf", "box", "violin", "qq"], "A numeric profile")
        if chosen == "kde":
            return variable.kde_figure(numeric, tokens), 300
        if chosen == "ecdf":
            return variable.ecdf_figure(numeric, tokens), 300
        if chosen == "box":
            return variable.box_from_profile(numeric, tokens), 200
        if chosen == "violin":
            return variable.violin_figure(numeric, tokens), 220
        return variable.qq_figure(numeric.get("qq"), tokens, "Normal quantiles (z)"), 340
    if profile.get("date"):
        _view(view, ["calendar"], "A date profile")
        return variable.calendar_figure(profile["date"].get("calendar", []), tokens), 220
    if profile.get("text"):
        _view(view, ["words"], "A text profile")
        return variable.horizontal_bars(profile["text"].get("words", []), tokens.text), 320
    raise PlotError("Draw a category's chart with ds.plot(column).")


def _model(run: dict[str, Any], target: str, view: str | None, tokens: Tokens) -> tuple[Built, int]:
    regression, classification = run.get("regression"), run.get("classification")
    shared = ["coefficients", "importances", "learning_curve"]
    if regression:
        chosen = _view(
            view, ["predicted", "residuals", "residual_histogram", *shared], "A regression"
        )
        if chosen == "predicted":
            return ml.predicted_figure(regression, target, tokens), 340
        if chosen == "residuals":
            return ml.residuals_figure(regression, tokens), 300
        if chosen == "residual_histogram":
            return ml.residual_histogram(regression, tokens), 260
    elif classification:
        views = ["confusion", "confusion_percent", "roc", "pr", "calibration", *shared]
        chosen = _view(view, views, "A classifier")
        if chosen in ("confusion", "confusion_percent"):
            percent = chosen == "confusion_percent"
            return ml.confusion_figure(classification, tokens, percent), 340
        if chosen == "roc":
            return ml.roc_figure(classification, tokens), 340
        if chosen == "pr":
            return ml.pr_figure(classification, tokens), 340
        if chosen == "calibration":
            return ml.calibration_figure(classification, tokens), 340
    else:
        raise PlotError("This model has no results to draw.")
    if chosen == "coefficients":
        if not run.get("coefficients"):
            raise PlotError("This model has no coefficients (not a linear model).")
        return ml.coefficients_figure(run["coefficients"], tokens), _rows_height(
            min(15, len(run["coefficients"]))
        )
    if chosen == "importances":
        if not run.get("importances"):
            raise PlotError("This model reports no importances (try model.explain()).")
        return ml.importances_figure(run["importances"], tokens), _rows_height(
            min(15, len(run["importances"]))
        )
    if not run.get("learning_curve"):
        raise PlotError("This model has no learning curve (iterative models only).")
    return ml.learning_curve_figure(run["learning_curve"], tokens), 280


def _explanation(
    found: dict[str, Any], view: str | None, options: dict[str, Any], tokens: Tokens
) -> tuple[Built, int]:
    chosen = _view(view, ["permutation", "shap", "dependence", "waterfall"], "An explanation")
    if chosen == "permutation":
        if not found.get("permutation"):
            raise PlotError("No permutation importance in this explanation.")
        items = found["permutation"]["items"]
        return ml.permutation_figure(found["permutation"], tokens), _rows_height(
            min(15, len(items))
        )
    shap = found.get("shap")
    if chosen == "shap":
        if not shap:
            raise PlotError(found.get("shap_unavailable") or "No SHAP values for this model.")
        return ml.beeswarm_figure(shap, tokens), _rows_height(len(shap["features"]), 34)
    if chosen == "waterfall":
        if not shap:
            raise PlotError(found.get("shap_unavailable") or "No SHAP values for this model.")
        row = options.get("row", shap["rows"][0] if shap["rows"] else 0)
        return ml.waterfall_figure(shap, row, tokens), 360
    dependence = found.get("dependence") or []
    column = options.get("column")
    chosen_curve = (
        next((d for d in dependence if d["column"] == column), None)
        if column
        else (dependence[0] if dependence else None)
    )
    if chosen_curve is None:
        names = ", ".join(d["column"] for d in dependence) or "none"
        raise PlotError(f"No partial dependence for {column!r}: columns {names}.")
    return ml.dependence_figure(chosen_curve, tokens), 320


def _synthetic(made: Any, view: str | None, tokens: Tokens) -> tuple[Built, int]:
    report = to_dict(made.report)
    views = ["mean", "std", "pca", "links", "links_real", "links_synthetic", "dcr", "scores"]
    if report.get("sequences"):
        views += ["acf", "samples"]
    chosen = _view(view, views, "Synthetic data")
    overview = report["overview"]
    if chosen in ("mean", "std"):
        return synthetic.mean_spread_figure(overview["mean_spread"], tokens, chosen), 340
    if chosen == "pca":
        if not overview.get("pca"):
            raise PlotError("No projection: fewer than two numeric columns.")
        return synthetic.pca_figure(overview["pca"], tokens), 360
    if chosen.startswith("links"):
        which = {"links": "gap", "links_real": "real", "links_synthetic": "synthetic"}[chosen]
        return synthetic.links_figure(report["links"], tokens, which), 420
    if chosen == "dcr":
        histogram = report["privacy"].get("histogram")
        if not histogram:
            raise PlotError("No distance histogram in this report.")
        return synthetic.dcr_figure(histogram, tokens), 300
    if chosen == "scores":
        return synthetic.scores_figure([(made.generation.method, report["scores"])], tokens), 300
    sequences = report["sequences"]
    if chosen == "acf":
        return synthetic.acf_figure(sequences["columns"][0], tokens), 280
    return synthetic.samples_figure(sequences["samples"][0], tokens), 300


def figure_data(
    result: Any, view: str | None = None, *, theme: Theme = "light", **options: Any
) -> tuple[Built, int]:
    """(plotly figure as a dict without the base layout, default height) for a result."""
    tokens = tokens_for(theme)
    kind = type(result).__name__

    if kind == "TrainedModel":
        return _model(to_dict(result), result.target, view, tokens)
    if kind == "SyntheticData":
        return _synthetic(result, view, tokens)
    if (
        isinstance(result, list)
        and result
        and all(type(r).__name__ in ("TrainedModel", "Failed") for r in result)
    ):
        runs = [(r.model, to_dict(r)) for r in result if type(r).__name__ == "TrainedModel"]
        if runs and runs[0][1].get("regression"):
            return ml.overlay_predicted_figure(runs, tokens), 360
        return ml.overlay_roc_figure(runs, tokens), 360

    data = to_dict(result)
    if kind == "Chart":
        analysis_type = options.get("analysis_type") or _infer_type(data)
        if view == "pie":  # a switch of the card, not a view the data is prepared for
            if data["kind"] != "bars":
                raise PlotError("A pie needs categories.")
            return charts.pie_figure(data, tokens), 300
        built = charts.chart_figure(data, analysis_type, tokens)
        if built is None:
            raise PlotError("No chart for identifiers and free text, as in the app.")
        return built, 280
    if kind == "VariableProfile":
        return _variable(data, view, tokens)
    if kind == "Fit":
        chosen = _view(view, ["qq", "laws"], "A fit")
        laws = data["laws"]
        if not laws:
            raise PlotError(data.get("reason") or "No law could be fitted.")
        if chosen == "laws":
            bins, count = options.get("bins"), options.get("count")
            if bins is None or count is None:
                raise PlotError("The laws need the histogram: use ds.plot(column, 'laws').")
            return variable.laws_figure(bins, data["grid"], laws[:3], count, tokens), 340
        law = next((x for x in laws if x["key"] == options.get("law")), laws[0])
        built = variable.qq_figure(
            {
                "theoretical": law["quantiles"],
                "sample": data["sample_quantiles"],
                "slope": 1,
                "intercept": 0,
            },
            tokens,
            f"{law['label']} quantiles",
        )
        return built, 340
    if kind == "Comparison":
        try:
            built = compare.comparison_figure(data, tokens, view, options.get("regression", True))
        except ValueError as error:
            raise PlotError(str(error)) from None
        return built, 420 if data["kind"] != "scatter" or not data.get("z") else 520
    if kind in ("Correlations", "Matrix"):
        matrix = data["matrix"] if kind == "Correlations" else data
        size = len(matrix["columns"])
        return variable.matrix_figure(matrix, tokens, options.get("clustered", True)), max(
            320, 40 + 28 * size
        )
    if kind == "SeriesOverview":
        layers = tuple(options.get("layers", ("values", "mean", "band")))
        return timeseries.overview_figure(
            data, tokens, layers, options.get("all_groups", False)
        ), 360
    if kind == "SeriesSeasonality":
        keys = [p["key"] for p in data["profiles"]] + (["overlay"] if data.get("overlay") else [])
        if not keys:
            raise PlotError(data.get("message") or "No seasonal pattern to draw.")
        chosen = _view(view, keys, "This seasonality")
        what = timeseries.value_label(data["setup"])
        if chosen == "overlay":
            return timeseries.overlay_figure(data["overlay"], what, tokens), 300
        profile = next(p for p in data["profiles"] if p["key"] == chosen)
        return timeseries.profile_figure(profile, what, tokens), 300
    if kind == "SeriesDecomposition":
        parts = data.get("result")
        if not parts:
            raise PlotError(data.get("message") or "No decomposition.")
        return timeseries.decomposition_figure(data, tokens), 140 * (3 + len(parts["seasonal"]))
    if kind == "SeriesStationarity":
        return timeseries.transformed_figure(data, tokens), 280
    if kind == "SeriesAutocorrelation":
        gram = data.get("correlogram")
        if not gram:
            raise PlotError(data.get("message") or "No correlogram.")
        chosen = _view(view, ["acf", "pacf"], "Autocorrelation")
        lags = gram["lags"] if chosen == "acf" else gram["lags"][: len(gram["pacf"])]
        return timeseries.correlogram_figure(lags, gram[chosen], gram["band"], tokens), 260
    if kind == "SeriesVolatility":
        return timeseries.volatility_figure(data, tokens), 360
    if kind == "SeriesResiduals":
        return timeseries.residuals_figure(data, tokens), 320
    if kind == "SeriesBreaks":
        return timeseries.breaks_figure(data, tokens), 340
    if kind == "SeriesForecast":
        return timeseries.forecast_figure(
            data, tokens, options.get("model"), options.get("overlay", False)
        ), 380
    if kind == "Explanation":
        return _explanation(data, view, options, tokens)
    if kind == "TuneProgress":
        chosen = _view(view, ["trials", "importance"], "A search")
        if chosen == "importance":
            if not data["importances"]:
                raise PlotError("Too few trials to rank the settings.")
            return ml.tuning_importance_figure(data["importances"], tokens), _rows_height(
                len(data["importances"]), 26
            )
        return ml.trials_figure(data, tokens), 300
    if kind == "KpiResult":
        built = kpi.kpi_figure(
            data,
            tokens,
            options.get("measure"),
            view or options.get("chart"),
            options.get("mode", "value"),
            options.get("labels", "auto"),
            options.get("hide_other", False),
            options.get("panel"),
        )
        height = (
            240
            if data["resolved"]["time"]
            else min(520, 70 + 26 * len((data["splits"] or [{"levels": [0] * 4}])[0]["levels"]))
        )
        return built, height
    if kind == "ColumnDetail":
        if data.get("levels") and not data.get("histogram"):
            return synthetic.levels_figure(data, tokens), min(520, 80 + 24 * len(data["levels"]))
        return synthetic.column_figure(data, tokens, view or "histogram"), 300
    if kind == "PairDetail":
        return synthetic.pair_figure(data, tokens), 320
    raise PlotError(f"No chart for {kind}.")


def plot(
    result: Any,
    view: str | None = None,
    *,
    theme: Theme = "light",
    title: str | None = None,
    height: int | None = None,
    **options: Any,
) -> Any:
    """A result drawn as the app draws it, as a plotly Figure (shown in a notebook cell).

    `view` picks among a result's charts (a comparison's box / violin / means, a model's
    predicted / residuals / roc / confusion…); `theme` is the app's light or dark one. Other
    options: `regression` (scatter), `layers` and `all_groups` (series overview), `model` and
    `overlay` (forecast), `column` and `row` (explanations), `measure`, `chart`, `mode`
    (KPI), `law` (fit)."""
    try:
        import plotly.graph_objects as go
    except ModuleNotFoundError:
        raise PlotError("Charts need plotly: pip install 'cyfouri-data-explorer[plot]'.") from None
    built, default_height = figure_data(result, view, theme=theme, **options)
    figure = compose(built, tokens_for(theme), height or default_height, title)
    return go.Figure(data=figure["data"], layout=figure["layout"])
