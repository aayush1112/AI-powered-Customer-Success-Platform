from __future__ import annotations


class CacheKeyBuilder:
    """Centralised Redis key construction — no hardcoded strings in endpoint code."""

    @staticmethod
    def customer_list_key(
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        industry: str | None,
        sort_by: str,
        sort_order: str,
    ) -> str:
        return (
            f"customers:list:{page}:{page_size}:"
            f"{search or ''}:{status or ''}:{industry or ''}:"
            f"{sort_by}:{sort_order}"
        )

    @staticmethod
    def customer_key(customer_id: object) -> str:
        return f"customer:{customer_id}"

    @staticmethod
    def customer_timeline_key(customer_id: object) -> str:
        return f"customer:timeline:{customer_id}"

    @staticmethod
    def interaction_key(interaction_id: object) -> str:
        return f"interaction:{interaction_id}"

    @staticmethod
    def insight_key(interaction_id: object) -> str:
        return f"insight:{interaction_id}"

    @staticmethod
    def dashboard_key(name: str) -> str:
        return f"dashboard:{name}"
