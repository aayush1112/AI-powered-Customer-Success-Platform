from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import (
    CustomerCreate,
    CustomerListParams,
    CustomerResponse,
    CustomerUpdate,
    PaginatedResponse,
)


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CustomerRepository(session)

    async def create(self, data: CustomerCreate, created_by: uuid.UUID) -> Customer:
        return await self._repo.create(
            company_name=data.company_name,
            industry=data.industry,
            contact_name=data.contact_name,
            contact_email=str(data.contact_email),
            contact_phone=data.contact_phone,
            created_by=created_by,
        )

    async def get_by_id(self, customer_id: uuid.UUID) -> Customer:
        customer = await self._repo.get_active_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer

    async def update(self, customer_id: uuid.UUID, data: CustomerUpdate) -> Customer:
        customer = await self.get_by_id(customer_id)
        updates = data.model_dump(exclude_none=True)
        if "contact_email" in updates:
            updates["contact_email"] = str(updates["contact_email"])
        if not updates:
            return customer
        return await self._repo.update(customer, **updates)

    async def delete(self, customer_id: uuid.UUID) -> None:
        customer = await self.get_by_id(customer_id)
        await self._repo.soft_delete(customer)

    async def get_paginated(
        self, params: CustomerListParams
    ) -> PaginatedResponse[CustomerResponse]:
        items, total = await self._repo.get_paginated(
            page=params.page,
            page_size=params.page_size,
            search=params.search,
            status=params.status,
            industry=params.industry,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        pages = max(1, (total + params.page_size - 1) // params.page_size)
        return PaginatedResponse(
            items=[CustomerResponse.model_validate(c) for c in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )
