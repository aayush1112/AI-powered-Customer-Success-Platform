from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.enums import CustomerStatus

T = TypeVar("T")

_SORTABLE_FIELDS = frozenset({"company_name", "created_at", "status", "updated_at"})
_SORT_ORDERS = frozenset({"asc", "desc"})


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class CustomerBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    industry: str | None = Field(None, max_length=100)
    contact_name: str = Field(..., min_length=1, max_length=200)
    contact_email: EmailStr
    contact_phone: str | None = Field(None, max_length=20)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    company_name: str | None = Field(None, min_length=1, max_length=255)
    industry: str | None = Field(None, max_length=100)
    contact_name: str | None = Field(None, min_length=1, max_length=200)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=20)
    status: CustomerStatus | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    industry: str | None
    contact_name: str
    contact_email: str
    contact_phone: str | None
    status: CustomerStatus
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CustomerCreateResponse(BaseModel):
    success: bool = True
    data: CustomerResponse


class CustomerUpdateResponse(BaseModel):
    success: bool = True
    data: CustomerResponse


class CustomerListParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    search: str | None = None
    status: CustomerStatus | None = None
    industry: str | None = None
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
