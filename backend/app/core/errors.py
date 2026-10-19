"""Domain errors carrying a message a user can act on, an error code and an HTTP status."""

from typing import Any


class AppError(Exception):
    def __init__(self, message: str, *, code: str = "app_error", status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        # Extra fields of the error body (e.g. the field to fix), added by subclasses.
        self.details: dict[str, Any] = {}
