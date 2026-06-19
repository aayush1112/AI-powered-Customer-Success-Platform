from __future__ import annotations


class CacheTTL:
    """Centralised TTL constants (seconds) for all cached resources."""

    CUSTOMER_LIST: int = 300
    CUSTOMER_DETAIL: int = 300
    INTERACTION_DETAIL: int = 300
    AI_INSIGHT: int = 600
    DASHBOARD: int = 300
