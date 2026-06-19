from __future__ import annotations

import json
from typing import Any

import structlog

logger = structlog.get_logger()

# ── JSON backend: orjson where available, stdlib fallback ────────────────────
try:
    import orjson

    def _dumps(obj: Any) -> str:
        return orjson.dumps(obj).decode()

    def _loads(raw: str | bytes) -> Any:
        return orjson.loads(raw)

except ImportError:
    def _dumps(obj: Any) -> str:  # type: ignore[misc]
        return json.dumps(obj, default=str)

    def _loads(raw: str | bytes) -> Any:  # type: ignore[misc]
        return json.loads(raw)


class CacheService:
    """High-level async cache with JSON serialisation and graceful Redis fallback.

    Every method catches *all* exceptions and returns a safe default value so
    that a Redis outage degrades to DB-only queries — it never turns into a 500.
    """

    def __init__(self) -> None:
        # Resolved lazily to avoid circular imports at module load time.
        from app.services.redis_service import redis_service  # noqa: PLC0415

        self._redis = redis_service

    @property
    def _client(self):  # type: ignore[return]
        """Raw aioredis client, or None when Redis is not connected."""
        return self._redis._client  # type: ignore[attr-defined]

    # ── JSON ops ──────────────────────────────────────────────────────────────

    async def get_json(self, key: str) -> Any | None:
        try:
            client = self._client
            if client is None:
                return None
            raw = await client.get(key)
            if raw is None:
                logger.debug("[CACHE MISS]", key=key)
                return None
            logger.debug("[CACHE HIT]", key=key)
            return _loads(raw)
        except Exception as exc:
            logger.warning("[CACHE ERROR] get_json", key=key, error=str(exc))
            return None

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> bool:
        try:
            client = self._client
            if client is None:
                return False
            serialized = _dumps(value)
            result = await client.set(key, serialized, ex=ttl)
            return bool(result)
        except Exception as exc:
            logger.warning("[CACHE ERROR] set_json", key=key, error=str(exc))
            return False

    # ── Key management ────────────────────────────────────────────────────────

    async def delete(self, *keys: str) -> int:
        try:
            client = self._client
            if client is None or not keys:
                return 0
            count = await client.delete(*keys)
            logger.info("[CACHE INVALIDATE]", keys=list(keys), count=count)
            return int(count)
        except Exception as exc:
            logger.warning("[CACHE ERROR] delete", keys=keys, error=str(exc))
            return 0

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching *pattern* (Redis SCAN + DELETE)."""
        try:
            client = self._client
            if client is None:
                return 0
            keys: list[str] = [k async for k in client.scan_iter(match=pattern)]
            if not keys:
                return 0
            count = await client.delete(*keys)
            logger.info("[CACHE INVALIDATE]", pattern=pattern, count=count)
            return int(count)
        except Exception as exc:
            logger.warning("[CACHE ERROR] delete_pattern", pattern=pattern, error=str(exc))
            return 0

    async def exists(self, key: str) -> bool:
        try:
            client = self._client
            if client is None:
                return False
            return bool(await client.exists(key))
        except Exception as exc:
            logger.warning("[CACHE ERROR] exists", key=key, error=str(exc))
            return False

    async def ttl(self, key: str) -> int:
        """Return remaining TTL in seconds. -2 = key missing, -1 = no TTL set."""
        try:
            client = self._client
            if client is None:
                return -2
            return int(await client.ttl(key))
        except Exception as exc:
            logger.warning("[CACHE ERROR] ttl", key=key, error=str(exc))
            return -2

    async def increment(self, key: str) -> int:
        try:
            client = self._client
            if client is None:
                return 0
            return int(await client.incr(key))
        except Exception as exc:
            logger.warning("[CACHE ERROR] increment", key=key, error=str(exc))
            return 0

    async def decrement(self, key: str) -> int:
        try:
            client = self._client
            if client is None:
                return 0
            return int(await client.decr(key))
        except Exception as exc:
            logger.warning("[CACHE ERROR] decrement", key=key, error=str(exc))
            return 0


# Module-level singleton — imported by endpoints and the decorator.
cache_service = CacheService()
