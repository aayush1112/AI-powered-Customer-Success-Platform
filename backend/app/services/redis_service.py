from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RedisService:
    """Thin async wrapper around the Redis client.

    Lifecycle: call connect() on startup, disconnect() on shutdown.
    All other methods require a live connection.
    """

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    # ── Lifecycle ─────────────────────────────────────────────

    async def connect(self) -> None:
        try:
            self._client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            await self._client.ping()
            logger.info("Redis connection established")
        except Exception as exc:
            logger.error("Failed to connect to Redis", error=str(exc))
            raise

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Redis connection closed")

    # ── Internal ──────────────────────────────────────────────

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis is not connected. Call connect() first.")
        return self._client

    # ── Public API ────────────────────────────────────────────

    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)
        except Exception as exc:
            logger.error("Redis GET failed", key=key, error=str(exc))
            raise

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        try:
            result = await self.client.set(key, value, ex=expire)
            return bool(result)
        except Exception as exc:
            logger.error("Redis SET failed", key=key, error=str(exc))
            raise

    async def delete(self, *keys: str) -> int:
        try:
            return await self.client.delete(*keys)
        except Exception as exc:
            logger.error("Redis DELETE failed", keys=keys, error=str(exc))
            raise

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    async def expire(self, key: str, seconds: int) -> bool:
        return bool(await self.client.expire(key, seconds))

    async def ping(self) -> bool:
        try:
            return bool(await self.client.ping())
        except Exception:
            return False


redis_service = RedisService()
