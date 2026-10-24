"""cyfouri-data-explorer: exploratory data analysis with statistical depth, in Python.

    import cyfouri_data_explorer as dx

    ds = dx.open("titanic.csv")
    ds.types                        # detected types, with the reasons
    ds.variable("Age")              # statistics, normality, outliers
    ds.compare("Age", "Survived")   # the test follows the types, with an effect size
    ds.correlations()               # mixed association matrix, ranked pairs, insights

The engine of the Data Explorer app: the same code computes the app's results.
"""

from cyfouri_data_explorer.catalog import ColumnView
from cyfouri_data_explorer.dataset import Dataset, DatasetInfo, from_arrow, from_pandas, open
from cyfouri_data_explorer.errors import ColumnNotFound, ExplorerError, NotFoundError
from cyfouri_data_explorer.filters.model import Condition
from cyfouri_data_explorer.typing.engine import DEFAULT_THRESHOLDS, Thresholds
from cyfouri_data_explorer.version import __version__

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
]
