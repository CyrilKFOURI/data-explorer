"""The app's charts in Python: every result draws as a plotly figure, with the app's theme."""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

import cyfouri_data_explorer as dx
from cyfouri_data_explorer.plots import PlotError
from cyfouri_data_explorer.plots.theme import DARK, LIGHT, format_number, with_alpha

go = pytest.importorskip("plotly.graph_objects")

SAMPLES = Path(__file__).resolve().parents[3] / "samples"


@pytest.fixture(scope="module")
def traps(tmp_path_factory: pytest.TempPathFactory) -> dx.Dataset:
    return dx.open(SAMPLES / "typing_traps.csv", cache_dir=tmp_path_factory.mktemp("traps"))


@pytest.fixture(scope="module")
def shop(tmp_path_factory: pytest.TempPathFactory) -> dx.Dataset:
    rng = np.random.default_rng(2)
    n = 300
    frame = pd.DataFrame(
        {"income": rng.normal(40_000, 9_000, n), "city": rng.choice(["Paris", "Lyon", "Nice"], n)}
    )
    frame["bought"] = np.where(frame["income"] + rng.normal(0, 5_000, n) > 42_000, "buy", "skip")
    frame["spend"] = frame["income"] * 0.02 + rng.normal(0, 60, n)
    return dx.from_pandas(frame, "shop", cache_dir=tmp_path_factory.mktemp("shop"))


def drawn(figure: Any) -> Any:
    assert isinstance(figure, go.Figure)
    assert figure.data, "the figure has no trace"
    return figure


def test_theme_helpers() -> None:
    assert with_alpha("#2a78d6", 0.5) == "rgba(42, 120, 214, 0.5)"
    assert format_number(1234.5) == "1,234" or format_number(1234.5) == "1,235"
    assert format_number(0.5) == "0.5" and format_number(2_000_000) == "2.00e+6"
    assert format_number(None) == "—"
    assert LIGHT.palette[0] != DARK.palette[0]


@pytest.mark.parametrize(
    ("column", "view", "trace"),
    [
        ("price_eur", None, "bar"),
        ("price_eur", "box", "box"),
        ("age", "kde", "scatter"),
        ("age", "ecdf", "scatter"),
        ("age", "violin", "violin"),
        ("age", "qq", "scatter"),
        ("price_eur", "laws", "bar"),
        ("city", None, "bar"),
        ("segment", "pie", "pie"),
        ("signup_date", None, "scatter"),
        ("last_login", "calendar", "heatmap"),
        ("comment", "words", "bar"),
    ],
)
def test_column_charts(traps: dx.Dataset, column: str, view: str | None, trace: str) -> None:
    figure = drawn(traps.plot(column, view))
    assert figure.data[0].type == trace


def test_column_chart_uses_the_type_colour_and_dark_theme(traps: dx.Dataset) -> None:
    light = traps.plot("price_eur")
    assert light.data[0].marker.color == LIGHT.numeric
    dark = traps.plot("price_eur", theme="dark", title="Price")
    assert dark.data[0].marker.color == DARK.numeric
    assert dark.layout.paper_bgcolor == DARK.surface
    assert dark.layout.title.text == "Price"


@pytest.mark.parametrize(
    ("x", "y", "view", "trace"),
    [
        ("income", "age", None, "scattergl"),
        ("income", "age", "density", "heatmap"),
        ("income", "segment", None, "box"),
        ("income", "segment", "violin", "violin"),
        ("income", "segment", "means", "scatter"),
        ("country", "segment", None, "heatmap"),
        ("country", "segment", "stacked", "bar"),
        ("signup_date", "income", None, "scatter"),
    ],
)
def test_comparisons_follow_the_types(
    traps: dx.Dataset, x: str, y: str, view: str | None, trace: str
) -> None:
    figure = drawn(dx.plot(traps.compare(x, y), view))
    assert trace in {t.type for t in figure.data}


def test_a_view_that_does_not_fit_is_refused(traps: dx.Dataset) -> None:
    with pytest.raises(PlotError, match="box, violin, means"):
        dx.plot(traps.compare("income", "segment"), "density")
    with pytest.raises(PlotError):
        dx.plot(traps.overview())  # no chart for the overview, as in the app


def test_correlation_matrix(traps: dx.Dataset) -> None:
    figure = drawn(dx.plot(traps.correlations()))
    assert figure.data[0].type == "heatmap" and figure.data[0].zmin == -1


def test_time_series_figures(tmp_path: Path) -> None:
    sales = dx.open(SAMPLES / "sales_timeseries.csv", cache_dir=tmp_path)
    series = sales.timeseries(time="date", value="revenue")
    drawn(dx.plot(series.overview()))
    season = series.seasonality()
    drawn(dx.plot(season, season.profiles[0].key))
    decomposition = drawn(dx.plot(series.decomposition()))
    assert decomposition.layout.yaxis.domain[0] >= 0
    drawn(dx.plot(series.stationarity("diff")))
    drawn(dx.plot(series.autocorrelation(), "pacf"))
    drawn(dx.plot(series.volatility()))
    drawn(dx.plot(series.residuals()))
    drawn(dx.plot(series.breaks()))


def test_model_figures(shop: dx.Dataset) -> None:
    classifier = shop.ml("bought").train()
    for view in (None, "confusion_percent", "roc", "pr", "calibration", "coefficients"):
        drawn(dx.plot(classifier, view))
    regressor = shop.ml("spend").train()
    for view in (None, "residuals", "residual_histogram"):
        drawn(dx.plot(regressor, view))
    with pytest.raises(PlotError):
        dx.plot(regressor, "roc")
    explained = classifier.explain()
    for view in ("permutation", "dependence"):
        drawn(dx.plot(explained, view))
    if explained.shap:
        drawn(dx.plot(explained, "shap"))
        drawn(dx.plot(explained, "waterfall"))
    forest = shop.ml("spend").train("decision_tree")
    drawn(dx.plot([regressor, forest]))


def test_synthetic_figures(traps: dx.Dataset) -> None:
    made = traps.synthetic(use_gpu=False).generate(rows=200)
    for view in ("mean", "std", "pca", "links", "links_real", "dcr", "scores"):
        drawn(dx.plot(made, view))
    drawn(dx.plot(made.column("age")))
    drawn(dx.plot(made.column("segment")))
    drawn(dx.plot(made.pair("income", "segment")))
    copula = traps.synthetic(use_gpu=False).generate("copula", rows=200)
    assert len(drawn(dx.plot([made, copula])).data) == 2  # scores of two runs side by side


def test_kpi_figure(tmp_path: Path) -> None:
    sales = dx.open(SAMPLES / "sales_timeseries.csv", cache_dir=tmp_path)
    suggested = sales.kpi_suggestions().kpis[1]
    result = sales.kpi(suggested.definition)
    drawn(dx.plot(result))
    by_store = sales.kpi({**suggested.definition.model_dump(), "groups": [{"column": "store"}]})
    assert len(drawn(dx.plot(by_store)).data) >= 2
    drawn(dx.plot(result, mode="change_pct"))
    share = drawn(dx.plot(by_store, "share"))
    assert share.layout.yaxis.ticksuffix == " %"
