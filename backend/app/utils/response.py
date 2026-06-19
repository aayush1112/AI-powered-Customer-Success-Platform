from __future__ import annotations

from typing import Any


def success(data: Any = None, message: str = "Success") -> dict:
    return {"success": True, "message": message, "data": data}


def failure(message: str, errors: list[Any] | None = None) -> dict:
    return {"success": False, "message": message, "errors": errors or []}
