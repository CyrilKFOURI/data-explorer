"""Synthetic data page (docs/pages/13-donnees-synthetiques.md)."""

from fastapi import FastAPI

from app.modules.synthetic.router import router
from app.modules.synthetic.service import SyntheticService


def setup(app: FastAPI) -> None:
    app.state.synthetic = SyntheticService(app.state.columns, app.state.workspace)
    app.state.datasets.after_import.append(app.state.synthetic.after_import)


__all__ = ["router", "setup"]
