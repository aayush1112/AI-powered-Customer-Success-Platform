from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.enums import UserRole

_SORTABLE_FIELDS = frozenset({"first_name", "email", "role", "is_active", "created_at"})
_SORT_ORDERS = frozenset({"asc", "desc"})


class UserListParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    search: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    sort_by: str = "created_at"
    sort_order: str = "desc"

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        if v not in _SORTABLE_FIELDS:
            allowed = ", ".join(sorted(_SORTABLE_FIELDS))
            raise ValueError(f"sort_by must be one of: {allowed}")
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        if v not in _SORT_ORDERS:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v


class UserUpdateRequest(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
