"""KPI builder page (docs/pages/12-kpi-builder.md)."""

from fastapi import FastAPI

from app.modules.kpi.router import router
from app.modules.kpi.service import KpiService


def setup(app: FastAPI) -> None:
    app.state.kpi = KpiService(app.state.columns, app.state.workspace)
    clearers = getattr(app.state, "settings", None)
    if clearers is not None:
        clearers.cache_clearers.append(app.state.kpi.clear)


__all__ = ["router", "setup"]
