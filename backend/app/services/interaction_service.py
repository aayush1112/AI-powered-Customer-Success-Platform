from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Interaction
from app.repositories.customer_repository import CustomerRepository
from app.repositories.interaction_repository import InteractionRepository
from app.schemas.customer import PaginatedResponse
from app.schemas.interaction import (
    CustomerTimelineResponse,
    InteractionCreate,
    InteractionListParams,
    InteractionResponse,
    InteractionUpdate,
)


class InteractionService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = InteractionRepository(session)
        self._customer_repo = CustomerRepository(session)

    async def create(
        self, data: InteractionCreate, created_by: uuid.UUID
    ) -> Interaction:
        customer = await self._customer_repo.get_active_by_id(data.customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        interaction = await self._repo.create(
            customer_id=data.customer_id,
            title=data.title,
            interaction_type=data.interaction_type,
            meeting_date=data.meeting_date,
            notes=data.notes,
            created_by=created_by,
        )
        # Re-fetch to load customer + created_by_user relationships
        result = await self._repo.get_with_relations(interaction.id)
        assert result is not None
        return result

    async def get_by_id(self, interaction_id: uuid.UUID) -> Interaction:
        interaction = await self._repo.get_with_relations(interaction_id)
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")
        return interaction

    async def update(
        self, interaction_id: uuid.UUID, data: InteractionUpdate
    ) -> Interaction:
        interaction = await self.get_by_id(interaction_id)
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return interaction
        await self._repo.update(interaction, **updates)
        result = await self._repo.get_with_relations(interaction_id)
        assert result is not None
        return result

    async def get_paginated(
        self, params: InteractionListParams
    ) -> PaginatedResponse[InteractionResponse]:
        items, total = await self._repo.get_paginated(
            page=params.page,
            page_size=params.page_size,
            search=params.search,
            customer_id=params.customer_id,
            interaction_type=params.interaction_type,
            start_date=params.start_date,
            end_date=params.end_date,
            created_by=params.created_by,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        pages = max(1, (total + params.page_size - 1) // params.page_size)
        return PaginatedResponse(
            items=[InteractionResponse.model_validate(i) for i in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )

    async def get_customer_timeline(
        self, customer_id: uuid.UUID
    ) -> CustomerTimelineResponse:
        customer = await self._customer_repo.get_active_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        interactions = await self._repo.get_by_customer_id(customer_id, limit=200)
        return CustomerTimelineResponse(
            customer_id=customer.id,
            company_name=customer.company_name,
            interactions=[InteractionResponse.model_validate(i) for i in interactions],
            total=len(interactions),
        )
