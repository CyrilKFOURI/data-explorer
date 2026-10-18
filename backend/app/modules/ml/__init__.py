"""Machine learning page (docs/pages/11-machine-learning.md)."""

from fastapi import FastAPI

from app.modules.ml.router import router
from app.modules.ml.service import MlService


def setup(app: FastAPI) -> None:
    app.state.ml = MlService(app.state.columns, app.state.workspace)


__all__ = ["router", "setup"]
