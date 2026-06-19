from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def cache_response(key_template: str, ttl: int = 300) -> Callable[[F], F]:
    """Decorator that caches the return value of an async function in Redis.

    ``key_template`` is a Python format string whose placeholders are filled
    from the wrapped function's parameter names, e.g.::

        @cache_response(key_template="customer:{customer_id}", ttl=300)
        async def get_customer(customer_id: uuid.UUID, ...) -> CustomerResponse:
            ...

    Behaviour:
    - Cache **hit** → returns the cached dict immediately (FastAPI validates it
      against ``response_model`` on the way out).
    - Cache **miss** → executes the wrapped function, serialises the result
      (Pydantic models → ``model_dump(mode="json")``), stores it, and returns
      the original value.
    - Works transparently with FastAPI's dependency-injection because
      ``functools.wraps`` preserves the original signature so ``inspect``
      still sees all ``Depends()`` parameters.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Late import — avoids circular dependency at module load time.
            from app.services.cache.service import cache_service  # noqa: PLC0415

            # Bind all positional + keyword args to their parameter names.
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            params: dict[str, Any] = dict(bound.arguments)
            params.pop("self", None)

            # Build cache key — every value is coerced to a plain string.
            safe = {k: str(v) for k, v in params.items()}
            try:
                cache_key = key_template.format(**safe)
            except KeyError:
                # Template references a name not in the signature; skip cache.
                return await func(*args, **kwargs)

            # ── Cache read ───────────────────────────────────────────
            cached = await cache_service.get_json(cache_key)
            if cached is not None:
                return cached

            # ── Cache miss: run the real function ────────────────────
            result = await func(*args, **kwargs)

            # ── Serialise for storage ────────────────────────────────
            if hasattr(result, "model_dump"):
                serializable: Any = result.model_dump(mode="json")
            elif isinstance(result, list) and result and hasattr(result[0], "model_dump"):
                serializable = [item.model_dump(mode="json") for item in result]
            else:
                serializable = result

            await cache_service.set_json(cache_key, serializable, ttl=ttl)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
