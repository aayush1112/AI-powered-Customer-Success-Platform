from __future__ import annotations

# Import order matters: each model must be imported after the models it
# references via ForeignKey, so SQLAlchemy can resolve the mapper graph.
from app.models.user import User
from app.models.customer import Customer
from app.models.interaction import Interaction
from app.models.ai_insight import AIInsight

__all__ = ["User", "Customer", "Interaction", "AIInsight"]
