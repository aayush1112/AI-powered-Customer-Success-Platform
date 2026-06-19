from __future__ import annotations

from app.repositories.ai_insight_repository import AIInsightRepository
from app.repositories.base import BaseRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "CustomerRepository",
    "InteractionRepository",
    "AIInsightRepository",
]
