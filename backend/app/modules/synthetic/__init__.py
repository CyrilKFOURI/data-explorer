"""Synthetic data page (docs/pages/13-donnees-synthetiques.md)."""

from fastapi import FastAPI

from app.modules.synthetic.agent_tools import agent_tools
from app.modules.synthetic.router import router
from app.modules.synthetic.service import SyntheticService


def setup(app: FastAPI) -> None:
    settings = getattr(app.state, "settings", None)

    def compute() -> tuple[str | None, bool]:
        """The card the deep methods may use, and whether "Use the GPU" allows it."""
        if settings is None:
            return None, False
        status = settings.gpu()
        card = status.name if status.state == "ready" and status.torch else None
        choice = settings.get().compute.use_gpu
        return card, card is not None if choice is None else choice

    app.state.synthetic = SyntheticService(app.state.columns, app.state.workspace, compute)
    app.state.datasets.after_import.append(app.state.synthetic.after_import)


__all__ = ["agent_tools", "router", "setup"]
