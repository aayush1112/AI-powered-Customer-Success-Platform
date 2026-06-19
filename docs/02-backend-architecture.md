# Backend Architecture

## Technology Stack

| Technology | Version | Role |
|-----------|---------|------|
| Python | 3.12 | Runtime |
| FastAPI | 0.115 | ASGI web framework |
| SQLAlchemy | 2.0 | ORM (async) |
| asyncpg | 0.30 | PostgreSQL async driver |
| Alembic | 1.14 | Database migrations |
| Pydantic v2 | 2.10 | Schema validation + settings |
| pydantic-settings | 2.7 | Environment config |
| structlog | 24.4 | Structured logging |
| python-jose | 3.3 | JWT encoding/decoding |
| bcrypt | 5.0 | Password hashing |
| redis-py | 5.2 | Redis client (async) |
| slowapi | 0.1 | Rate limiting |
| google-generativeai | 0.8 | Gemini AI SDK |
| uvicorn | 0.32 | ASGI server |

---

## Layer Architecture

```
HTTP Request
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Middleware Stack (applied in reverse registration     │
│  order — last registered runs first)                  │
│  1. SecurityHeadersMiddleware  ← outermost             │
│  2. LoggingMiddleware (assigns request_id, logs)       │
│  3. SlowAPIMiddleware (rate limiting)                  │
│  4. CORSMiddleware                                     │
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Router  (app/api/v1/endpoints/*.py)                   │
│  - Path parameters, query params, request bodies      │
│  - FastAPI Depends: get_db, require_role(...)          │
│  - No business logic                                  │
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Service  (app/services/*.py)                          │
│  - All business rules and validations                  │
│  - Orchestrates repository calls                       │
│  - Calls AI client, cache service                      │
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Repository  (app/repositories/*.py)                   │
│  - SQLAlchemy async queries only                       │
│  - Returns ORM model instances                         │
│  - No business logic                                   │
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│  Database / Cache                                      │
│  PostgreSQL 16 (primary) + Redis 7 (cache)            │
└────────────────────────────────────────────────────────┘
```

---

## Key Modules

### `app/core/config.py` — Settings
Pydantic `BaseSettings` reads all configuration from environment variables. Startup validators reject:
- `SECRET_KEY` equal to the default placeholder
- `SECRET_KEY` shorter than 32 characters
- Invalid `DATABASE_URL` driver prefix (auto-corrected to `asyncpg`)

### `app/core/security.py` — JWT
- **Access token**: 15 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh token**: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- Both tokens embed a `type` claim (`"access"` / `"refresh"`) to prevent token substitution attacks.
- bcrypt password hashing with per-user salt via `bcrypt.gensalt()`.

### `app/core/logging.py` — Structlog
- Development: coloured console output
- Production: JSON renderer → stdout (captured by container runtime)
- All processors: `merge_contextvars`, logger name, log level, ISO timestamp, stack info
- Third-party noise suppressed: `uvicorn.access` → WARNING, `sqlalchemy.engine` → WARNING in non-debug mode

### `app/middleware/logging.py` — Request logging
Assigns a UUID `request_id` per request, binds it to structlog context vars so every log line within the request carries the ID. Emits `request_started` and `request_completed` events with method, path, status code, and duration.

### `app/middleware/security.py` — Security headers
Adds `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Referrer-Policy`, and `Permissions-Policy` to every response without modifying any business logic.

### `app/api/deps.py` — Dependency injection
- `get_db()` — yields an `AsyncSession` per request (auto-committed on success, rolled back on error)
- `get_current_user()` — decodes Bearer JWT, fetches User from DB
- `require_role(*roles)` — factory returning a `Depends(...)` that raises `ForbiddenException` if the user's role is not in the allowed set

### `app/services/cache/` — Redis cache layer
- `CacheService` — thin async wrapper around `redis.asyncio.Redis`
- `cached()` decorator — cache-aside pattern: check Redis first, fall back to function, store result with TTL
- `CacheTTL` constants — defined in `ttl.py`; dashboard metrics cache for 5 minutes, customer lists for 2 minutes
- `CacheKey` — typed key builder in `keys.py`

### `app/services/ai/` — Gemini integration
- `GeminiClient` — wraps `google.generativeai` with exponential backoff retry (up to `GEMINI_MAX_RETRIES` attempts)
- `prompts.py` — builds structured prompts from interaction + customer data
- Falls back to a canned "fallback" insight when Gemini is unreachable and `GEMINI_API_KEY` is empty or the call fails all retries

---

## Database Session Management

```python
# Session lifecycle per request
async with AsyncSession(engine) as session:
    async with session.begin():
        # all DB operations
        ...
    # auto-commit on __aexit__ success
    # auto-rollback on exception
```

Connection pool: `pool_size=10`, `max_overflow=20` (configurable via env vars). Pool pre-ping enabled to detect stale connections.

---

## Error Hierarchy

```
AppException (base, 500)
├── NotFoundException         (404)
├── ConflictException         (409)
├── UnauthorizedException     (401)
└── ForbiddenException        (403)
```

Exception handlers registered in `app/exceptions/handlers.py` convert all `AppException` subclasses to structured JSON: `{"success": false, "message": "...", "errors": [...]}`. Unhandled exceptions return 500 with the same shape but no internal detail.

---

## API Documentation

FastAPI auto-generates OpenAPI 3.0 docs:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`
- JSON spec: `http://localhost:8000/api/v1/openapi.json`

---

## Test Architecture

| Layer | Framework | Location |
|-------|-----------|----------|
| Unit | pytest + pytest-mock | `tests/unit/` |
| Integration/API | pytest + httpx AsyncClient + real DB/Redis | `tests/test_*.py` |

Coverage threshold: **85%** (enforced by `--cov-fail-under=85` in CI).
