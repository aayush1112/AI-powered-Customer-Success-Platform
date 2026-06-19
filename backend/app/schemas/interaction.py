from __future__ import annotations

import uuid
from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import InteractionType

T = TypeVar("T")

_SORTABLE_FIELDS = frozenset({"meeting_date", "created_at", "title"})
_SORT_ORDERS = frozenset({"asc", "desc"})


class InteractionCustomerNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str


class InteractionCreatedByNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str


class InteractionCreate(BaseModel):
    customer_id: uuid.UUID
    title: str = Field(..., min_length=3, max_length=255)
    interaction_type: InteractionType
    meeting_date: datetime
    notes: str = Field(..., min_length=10, max_length=10000)


class InteractionUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    interaction_type: InteractionType | None = None
    meeting_date: datetime | None = None
    notes: str | None = Field(None, min_length=10, max_length=10000)


class InteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    title: str
    interaction_type: InteractionType
    meeting_date: datetime
    notes: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    customer: InteractionCustomerNested
    created_by_user: InteractionCreatedByNested | None


class InteractionCreateResponse(BaseModel):
    success: bool = True
    data: InteractionResponse


class InteractionUpdateResponse(BaseModel):
    success: bool = True
    data: InteractionResponse


class InteractionListParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    search: str | None = None
    customer_id: uuid.UUID | None = None
    interaction_type: InteractionType | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_by: uuid.UUID | None = None
    sort_by: str = "meeting_date"
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


class CustomerTimelineResponse(BaseModel):
    customer_id: uuid.UUID
    company_name: str
    interactions: list[InteractionResponse]
    total: int
