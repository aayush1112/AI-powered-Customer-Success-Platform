from __future__ import annotations

from app.schemas.dashboard import (
    ActionItem,
    CustomerStatusBreakdown,
    DashboardMetrics,
    DashboardPeriod,
    InteractionTrendPoint,
    InteractionTypeBreakdown,
    RecentActivityItem,
    RiskItem,
    SentimentBreakdown,
)
from app.schemas.ai_insight import (
    AIInsightGenerateResponse,
    AIInsightResponse,
    GeminiInsightOutput,
)
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from app.schemas.customer import (
    CustomerCreate,
    CustomerCreateResponse,
    CustomerListParams,
    CustomerResponse,
    CustomerUpdate,
    CustomerUpdateResponse,
    PaginatedResponse,
)
from app.schemas.interaction import (
    CustomerTimelineResponse,
    InteractionCreate,
    InteractionCreateResponse,
    InteractionListParams,
    InteractionResponse,
    InteractionUpdate,
    InteractionUpdateResponse,
)

__all__ = [
    # dashboard
    "DashboardMetrics",
    "DashboardPeriod",
    "CustomerStatusBreakdown",
    "InteractionTrendPoint",
    "InteractionTypeBreakdown",
    "SentimentBreakdown",
    "RiskItem",
    "ActionItem",
    "RecentActivityItem",
    # ai insight
    "AIInsightResponse",
    "AIInsightGenerateResponse",
    "GeminiInsightOutput",
    # auth
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "TokenResponse",
    "AccessTokenResponse",
    "UserResponse",
    "RegisterResponse",
    "MessageResponse",
    # customer
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerCreateResponse",
    "CustomerUpdateResponse",
    "CustomerListParams",
    "PaginatedResponse",
    # interaction
    "InteractionCreate",
    "InteractionUpdate",
    "InteractionResponse",
    "InteractionCreateResponse",
    "InteractionUpdateResponse",
    "InteractionListParams",
    "CustomerTimelineResponse",
]
