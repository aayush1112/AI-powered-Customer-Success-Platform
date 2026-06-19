from __future__ import annotations

import enum


class CustomerStatus(str, enum.Enum):
    """Lifecycle status of a customer account."""

    ACTIVE = "ACTIVE"
    AT_RISK = "AT_RISK"
    CHURNED = "CHURNED"
    PROSPECT = "PROSPECT"
