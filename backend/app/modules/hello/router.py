from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["module:hello"])


class HelloOut(BaseModel):
    message: str


@router.get("")
def hello() -> HelloOut:
    return HelloOut(message="Hello from the demo module")
