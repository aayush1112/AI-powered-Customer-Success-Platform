from __future__ import annotations

import enum

from pydantic import BaseModel


class DashboardPeriod(str, enum.Enum):
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    ALL_TIME = "all_time"


class DashboardMetrics(BaseModel):
    total_customers: int = 0
    active_customers: int = 0
    at_risk_customers: int = 0
    churned_customers: int = 0
    total_interactions: int = 0
    interactions_this_month: int = 0
    positive_insights: int = 0
    neutral_insights: int = 0
    negative_insights: int = 0


class CustomerStatusBreakdown(BaseModel):
    ACTIVE: int = 0
    AT_RISK: int = 0
    CHURNED: int = 0
    PROSPECT: int = 0


class InteractionTrendPoint(BaseModel):
    date: str
    count: int


class InteractionTypeBreakdown(BaseModel):
    MEETING: int = 0
    CALL: int = 0
    EMAIL: int = 0
    QBR: int = 0


class SentimentBreakdown(BaseModel):
    POSITIVE: int = 0
    NEUTRAL: int = 0
    NEGATIVE: int = 0


class RiskItem(BaseModel):
    risk: str
    count: int


class ActionItem(BaseModel):
    action: str
    count: int


class RecentActivityItem(BaseModel):
    type: str  # "customer" | "interaction" | "insight"
    title: str
    subtitle: str | None = None
    timestamp: str  # ISO datetime string
