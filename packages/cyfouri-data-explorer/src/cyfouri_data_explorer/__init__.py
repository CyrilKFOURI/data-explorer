"""cyfouri-data-explorer: exploratory data analysis with statistical depth, in Python.

    import cyfouri_data_explorer as dx

    ds = dx.open("titanic.csv")
    ds.types                        # detected types, with the reasons
    ds.variable("Age")              # statistics, normality, outliers
    ds.compare("Age", "Survived")   # the test follows the types, with an effect size
    ds.correlations()               # mixed association matrix, ranked pairs, insights
    dx.plot(ds.compare("Age", "Survived"))   # the app's chart (the plot extra)

The engine of the Data Explorer app: the same code computes the app's results.
"""

from cyfouri_data_explorer.catalog import ColumnView
from cyfouri_data_explorer.dataset import Dataset, DatasetInfo, from_arrow, from_pandas, open
from cyfouri_data_explorer.errors import ColumnNotFound, ExplorerError, NotFoundError
from cyfouri_data_explorer.filters.model import Condition
from cyfouri_data_explorer.results import to_dict, to_pandas
from cyfouri_data_explorer.typing.engine import DEFAULT_THRESHOLDS, Thresholds
from cyfouri_data_explorer.version import __version__


def plot(result: object, view: str | None = None, **options: object) -> object:
    """A result drawn as the app draws it, as a plotly Figure (the `plot` extra); see
    `cyfouri_data_explorer.plots.plot`."""
    from cyfouri_data_explorer.plots import plot as draw

    return draw(result, view, **options)  # type: ignore[arg-type]


__all__ = [
    "DEFAULT_THRESHOLDS",
    "ColumnNotFound",
    "ColumnView",
    "Condition",
    "Dataset",
    "DatasetInfo",
    "ExplorerError",
    "NotFoundError",
    "Thresholds",
    "__version__",
    "from_arrow",
    "from_pandas",
    "open",
    "plot",
    "to_dict",
    "to_pandas",
]
