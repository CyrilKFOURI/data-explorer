"""Time series page: one series, analysed section by section.

See docs/pages/10-series-temporelles.md.
"""

from fastapi import FastAPI

from app.modules.timeseries.router import router
from app.modules.timeseries.service import TimeSeriesService


def setup(app: FastAPI) -> None:
    app.state.timeseries = TimeSeriesService(app.state.columns)
    clearers = getattr(app.state, "settings", None)
    if clearers is not None:
        clearers.cache_clearers.append(app.state.timeseries.clear)


__all__ = ["router", "setup"]
