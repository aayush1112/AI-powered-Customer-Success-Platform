# Redis Caching Strategy

## Overview

Redis 7 is used as a **cache-aside** store with TTL-based expiration. The backend reads from Redis before hitting PostgreSQL, and writes to PostgreSQL first before invalidating or updating the cache. No write-through is used — the cache is a read optimisation only.

Redis is also used to enforce **rate limiting** state via SlowAPI.

---

## Cache Layer Architecture

```
Request
  │
  ▼
Service.method()
  │
  ├─► CacheService.get(key)
  │     ├─► HIT  → deserialise → return (no DB call)
  │     └─► MISS → fall through
  │
  ├─► Repository.query() → PostgreSQL
  │
  └─► CacheService.set(key, value, ttl)
        └─► return value
```

On write operations:
```
Service.update() / create() / delete()
  ├─► Repository.update() → PostgreSQL (always first)
  └─► CacheService.delete(key) / CacheService.delete_pattern(prefix)
```

---

## Module Structure

```
app/services/cache/
├── __init__.py      exports: CacheService, cached, CacheTTL, CacheKey
├── service.py       CacheService class (async Redis wrapper)
├── decorator.py     @cached() decorator
├── keys.py          CacheKey typed key builder
└── ttl.py           TTL constants
```

### `CacheService` (`service.py`)
Thin async wrapper around `redis.asyncio.Redis`:
- `get(key)` → JSON-deserialised value or `None`
- `set(key, value, ttl)` → JSON-serialised, stored with EX
- `delete(key)` → explicit invalidation
- `delete_pattern(pattern)` → SCAN + DEL (used for prefix invalidation)
- `ping()` → `PING` command (used by health check)
- `connect()` / `disconnect()` → lifecycle hooks called in `lifespan`

### `@cached()` Decorator (`decorator.py`)
Wraps async service methods with cache-aside logic. Used on methods that:
- Read data without side effects
- Can tolerate slightly stale data for the TTL period

### `CacheTTL` Constants (`ttl.py`)

| Constant | Value | Used For |
|----------|-------|----------|
| `DASHBOARD` | 5 minutes | Dashboard aggregate metrics |
| `CUSTOMER_LIST` | 2 minutes | Paginated customer list responses |
| `CUSTOMER_DETAIL` | 5 minutes | Individual customer detail |
| `INTERACTION_LIST` | 2 minutes | Interaction list per customer |

### `CacheKey` Builder (`keys.py`)
Type-safe key construction to avoid collisions:
- `CacheKey.customer_list(page, page_size, filters)` → `"csp:customers:list:p1:ps10:..."`
- `CacheKey.customer(id)` → `"csp:customers:{uuid}"`
- `CacheKey.dashboard_metrics()` → `"csp:dashboard:metrics"`
- Consistent prefix `csp:` scopes all keys to this application

---

## Cache Invalidation Rules

| Operation | Keys Invalidated |
|-----------|-----------------|
| `POST /customers` | `csp:customers:list:*` (all list pages) |
| `PUT /customers/{id}` | `csp:customers:{id}`, `csp:customers:list:*` |
| `DELETE /customers/{id}` | `csp:customers:{id}`, `csp:customers:list:*` |
| `POST /interactions` | `csp:interactions:customer:{customer_id}:*` |
| `PUT /interactions/{id}` | `csp:interactions:{id}`, related list keys |
| Insight generated | `csp:dashboard:*` (sentiment/action counts change) |

---

## Redis Configuration (Production)

From `deployment/docker-compose.production.yml`:

```yaml
command: redis-server
  --requirepass ${REDIS_PASSWORD}
  --appendonly yes           # AOF persistence
  --appendfsync everysec     # fsync every second (balanced durability)
  --maxmemory 256mb          # bounded memory
  --maxmemory-policy allkeys-lru  # evict LRU keys when full
  --loglevel warning
```

**`allkeys-lru`** is intentional: if Redis fills up, it evicts the least-recently-used keys. Since Redis is a cache (not primary storage), data loss is tolerable — the system falls back to PostgreSQL on cache miss.

---

## Rate Limiting via Redis

SlowAPI uses Redis to track request counts per IP address across distributed instances:

```python
# app/core/rate_limit.py
limiter = Limiter(key_func=get_remote_address)
```

Limits are applied per endpoint:
- `/auth/login`, `/auth/register` — stricter limits (Nginx + SlowAPI)
- All other authenticated endpoints — general limit

When Redis is unavailable, rate limiting falls back to in-memory state (single process only). This is acceptable for development but production deployments should always have Redis running.

---

## Monitoring Cache Performance

Key metrics to watch (via Redis INFO or a Prometheus Redis exporter):
- `keyspace_hits` / `keyspace_misses` → hit ratio target: >70%
- `used_memory` → should stay under `maxmemory` (256 MB)
- `evicted_keys` → if non-zero, consider increasing `maxmemory`
- `connected_clients` → should not spike unexpectedly

Recommended tooling: **Redis Exporter** + **Prometheus** + **Grafana** dashboard (Redis template ID: 763).
