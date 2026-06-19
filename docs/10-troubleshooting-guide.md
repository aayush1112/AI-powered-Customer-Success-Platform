# Troubleshooting Guide

## Quick Diagnostics

Run this first to understand the overall system state:

```bash
# Check all container statuses
docker compose ps

# View logs from all services (last 50 lines each)
docker compose logs --tail=50

# Check health endpoints
curl http://localhost:8000/api/v1/health | jq .
curl http://localhost:8000/api/v1/readiness | jq .
curl http://localhost:8000/api/v1/liveness | jq .
```

---

## Common Issues

### Backend won't start

**Symptom:** `csp_backend` container exits immediately or enters restart loop.

**Check:**
```bash
docker compose logs backend --tail=100
```

**Common causes:**

| Error in logs | Fix |
|--------------|-----|
| `SECRET_KEY must be changed from the default value` | Set a real SECRET_KEY in `backend/.env` (min 32 chars) |
| `could not connect to server` (PostgreSQL) | Wait for postgres to be ready; check `docker compose ps postgres` |
| `Connection refused` (Redis) | Check Redis container is healthy; check REDIS_URL in .env |
| `ModuleNotFoundError` | Rebuild the image: `docker compose build backend` |

---

### Database migration fails

**Symptom:** `alembic upgrade head` exits with error.

```bash
docker compose exec backend alembic upgrade head
```

**Common causes:**

| Error | Fix |
|-------|-----|
| `relation already exists` | Migration partially applied; check `alembic history` and `alembic current` |
| `Connection refused` | Postgres not running; start it first |
| `ssl connection is required` | Add `?ssl=require` to DATABASE_URL for managed databases |
| `permission denied` | DB user lacks CREATE TABLE privilege; check user roles |

**Recovery:**
```bash
# Check current state
docker compose exec backend alembic current
docker compose exec backend alembic history --verbose

# Mark a specific revision as current (use with care)
docker compose exec backend alembic stamp <revision_id>
```

---

### Frontend shows "API error" or won't load

**Symptom:** Frontend loads but API calls fail; browser console shows CORS errors or network errors.

**Check:**
```bash
# Is the backend running?
curl http://localhost:8000/api/v1/liveness

# Are CORS origins correct?
# backend/.env must include the frontend origin:
ALLOWED_ORIGINS=["http://localhost:3000"]
```

**Common causes:**

| Symptom | Fix |
|---------|-----|
| `CORS error` in browser | Add frontend origin to `ALLOWED_ORIGINS` in backend/.env |
| `Connection refused` | Backend not running or wrong port |
| `401 Unauthorized` on all requests | Clear localStorage: `localStorage.clear()` then re-login |
| Blank page | Check frontend container logs; may be a build error |

---

### Login returns 422 Unprocessable Entity

**Symptom:** POST to `/api/v1/auth/login` returns 422.

**Cause:** Request body validation failed. Check the response body for field-level errors:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "wrong"}' | jq .
```

The `errors` array in the response identifies which fields failed.

---

### AI insight generation fails

**Symptom:** POST to `/api/v1/insights/generate/{id}` returns 500 or returns a fallback insight.

**Check:**
```bash
# Verify GEMINI_API_KEY is set
docker compose exec backend env | grep GEMINI

# Test the API key manually
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

**Common causes:**

| Symptom | Fix |
|---------|-----|
| `is_fallback: true` in response | GEMINI_API_KEY is empty or invalid |
| `ResourceExhausted` in logs | Rate limit hit; retry after 60 seconds |
| `InvalidArgument` | Model name wrong; default is `gemini-2.5-flash` |
| Timeout after 30s | Network issue reaching Google API; check outbound connectivity |

---

### Redis health check fails

**Symptom:** `/api/v1/health` returns `"redis": "unhealthy"`.

```bash
# Check Redis is running
docker compose ps redis

# Test Redis directly
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} ping

# Check REDIS_URL format
# Correct: redis://:password@redis:6379/0
# Wrong: redis://redis:6379/0 (missing password for protected Redis)
```

---

### Docker build fails

**Symptom:** `docker compose build` exits with error.

**Backend:**
```bash
docker build ./backend --target development --no-cache
```
Common issues:
- `pip install` fails → check internet connectivity from Docker build context
- `COPY` fails → check files exist at expected paths

**Frontend:**
```bash
docker build ./frontend --target builder --no-cache
```
Common issues:
- `npm ci` fails → `package-lock.json` out of sync; run `npm install` locally and commit the lock file
- Next.js build fails → check for TypeScript errors: `npm run type-check`

---

### Tests fail in CI but pass locally

**Common causes:**

1. **Missing env vars in CI** — Check the CI workflow env section. Unit tests need `SECRET_KEY`, `DATABASE_URL`, etc.
2. **Port already in use** — CI services (Postgres, Redis) conflict with system services; check port mappings in workflow.
3. **Async test isolation** — Each test should use an isolated transaction; check `conftest.py` for session fixture.
4. **Time-dependent tests** — Tests depending on `datetime.now()` can be flaky; use a fixed datetime.

---

### High memory usage

**Check:**
```bash
docker stats --no-stream
```

**Common causes:**

| Service | Cause | Fix |
|---------|-------|-----|
| Redis | No maxmemory set | Set `--maxmemory 256mb --maxmemory-policy allkeys-lru` |
| PostgreSQL | Too many connections | Add PgBouncer; reduce `DATABASE_POOL_SIZE` |
| Backend | Memory leak | Restart backend; check for unclosed file handles |
| Frontend | Next.js dev mode | Use production build in production |

---

## Log Locations

| Service | Log access |
|---------|-----------|
| Backend | `docker compose logs backend` |
| Frontend | `docker compose logs frontend` |
| PostgreSQL | `docker compose logs postgres` |
| Redis | `docker compose logs redis` |
| Nginx (prod) | `docker compose -f deployment/docker-compose.production.yml logs nginx` |
| Application (structured) | Pipe backend logs through `jq` for JSON parsing |

**Parse structured backend logs:**
```bash
docker compose logs backend 2>&1 | grep '{' | jq -r '[.timestamp, .level, .event] | @tsv'
```

---

## Useful Commands

```bash
# Restart a single service
docker compose restart backend

# Rebuild and restart
docker compose up --build -d backend

# Connect to PostgreSQL
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# Connect to Redis CLI
docker compose exec redis redis-cli -a ${REDIS_PASSWORD}

# Clear all Redis keys (CAUTION — drops all cache)
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} FLUSHDB

# Check database table counts
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} \
  -c "SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"

# Run backend tests
docker compose exec backend pytest tests/ -v --tb=short

# Check Alembic migration status
docker compose exec backend alembic current
```
