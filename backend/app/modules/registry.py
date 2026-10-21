"""Optional modules. Adding a module = creating its package and listing it here."""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter, FastAPI

from app.modules import agent, kpi, ml, synthetic, timeseries


@dataclass(frozen=True)
class Module:
    id: str
    router: APIRouter
    setup: Callable[[FastAPI], None] | None = None  # creates the module's services on app.state


MODULES: list[Module] = [
    Module(id="timeseries", router=timeseries.router, setup=timeseries.setup),
    Module(id="ml", router=ml.router, setup=ml.setup),
    Module(id="kpi", router=kpi.router, setup=kpi.setup),
    Module(id="synthetic", router=synthetic.router, setup=synthetic.setup),
    Module(id="agent", router=agent.router, setup=agent.setup),
]


def mount_modules(app: FastAPI, prefix: str, modules: list[Module] | None = None) -> None:
    for module in MODULES if modules is None else modules:
        if module.setup is not None:
            module.setup(app)
        app.include_router(module.router, prefix=f"{prefix}/modules/{module.id}")
