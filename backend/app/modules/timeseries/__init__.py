"""Time series page: one series, analysed section by section.

See docs/pages/10-series-temporelles.md.
"""

from cyfouri_data_explorer.timeseries.service import TimeSeriesService
from fastapi import FastAPI

from app.modules.timeseries.agent_tools import agent_tools
from app.modules.timeseries.router import router


def setup(app: FastAPI) -> None:
    app.state.timeseries = TimeSeriesService(app.state.columns)
    clearers = getattr(app.state, "settings", None)
    if clearers is not None:
        clearers.cache_clearers.append(app.state.timeseries.clear)


__all__ = ["agent_tools", "router", "setup"]
