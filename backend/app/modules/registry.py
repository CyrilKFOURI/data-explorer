"""Optional modules. Adding a module = creating its package and listing it here."""

from dataclasses import dataclass

from fastapi import APIRouter, FastAPI

from app.modules import hello


@dataclass(frozen=True)
class Module:
    id: str
    router: APIRouter


MODULES: list[Module] = [
    Module(id="hello", router=hello.router),
]


def mount_modules(app: FastAPI, prefix: str, modules: list[Module] | None = None) -> None:
    for module in MODULES if modules is None else modules:
        app.include_router(module.router, prefix=f"{prefix}/modules/{module.id}")
