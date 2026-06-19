from __future__ import annotations

from http import HTTPStatus
from typing import Any


class AppException(Exception):
    """Base application exception.  All domain errors should subclass this."""

    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        errors: list[Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.errors: list[Any] = errors or []
        super().__init__(self.message)


class ValidationException(AppException):
    def __init__(
        self,
        message: str = "Validation failed",
        errors: list[Any] | None = None,
    ) -> None:
        super().__init__(message, HTTPStatus.UNPROCESSABLE_ENTITY, errors)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, HTTPStatus.NOT_FOUND)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, HTTPStatus.UNAUTHORIZED)


class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__(message, HTTPStatus.FORBIDDEN)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, HTTPStatus.CONFLICT)


class ServiceUnavailableException(AppException):
    def __init__(self, message: str = "Service temporarily unavailable") -> None:
        super().__init__(message, HTTPStatus.SERVICE_UNAVAILABLE)
