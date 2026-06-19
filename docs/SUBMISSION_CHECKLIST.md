# Submission Checklist

## AI-Powered Customer Success Platform

**Date:** 2026-06-19
**Version:** 1.0.0

Use this checklist before submitting or releasing the platform. Each item should be manually verified in a clean environment.

---

## 1. Environment Setup

- [ ] `.env.example` exists at root with all docker-compose variables documented
- [ ] `backend/.env.example` exists with all backend variables documented
- [ ] `frontend/.env.example` exists with all frontend variables documented
- [ ] No real secrets are committed to version control (check with `git log -p | grep -i "secret\|password\|key"`)
- [ ] `SECRET_KEY` is set to a non-default value with at least 32 characters
- [ ] `GEMINI_API_KEY` is set and valid

---

## 2. Core Features

### ✓ Authentication & RBAC

- [ ] User can register a new account at `/register`
- [ ] User can log in at `/login` with correct credentials
- [ ] Login returns access token + refresh token
- [ ] Invalid credentials return 401 (not 500)
- [ ] Deactivated user cannot log in (returns 403)
- [ ] Logout clears session and redirects to `/login`
- [ ] Protected pages redirect unauthenticated users to `/login`
- [ ] Token refresh works transparently (re-login not required after 15 minutes)

### ✓ Customer CRUD

- [ ] Can create a new customer via the form
- [ ] Paginated customer list loads correctly
- [ ] Can search customers by company name / contact name / email
- [ ] Can filter customers by status (ACTIVE, AT_RISK, CHURNED, PROSPECT)
- [ ] Can view individual customer detail page
- [ ] Can edit customer information
- [ ] Can delete a customer (and all related interactions/insights cascade)

### ✓ Interaction CRUD

- [ ] Can log a new interaction (CALL, EMAIL, MEETING, NOTE)
- [ ] Interactions appear in the customer timeline
- [ ] Can edit an existing interaction
- [ ] Can delete an interaction

### ✓ AI Insights (Gemini)

- [ ] Can generate an insight for an interaction
- [ ] Insight shows: summary, sentiment badge, action items list, risks list
- [ ] Can regenerate an insight
- [ ] Fallback insight shown when Gemini is unavailable (not a 500 error)
- [ ] `is_fallback: true` appears in API response when Gemini fails

### ✓ Dashboard Analytics

- [ ] Dashboard loads with: KPI cards, customer status chart, interaction volume chart, sentiment chart
- [ ] At-risk customers section lists customers with AI-identified risks
- [ ] Action items section shows pending Gemini recommendations
- [ ] Recent activity shows latest 10 interactions

### ✓ Redis Caching

- [ ] Dashboard metrics are cached (second load is faster)
- [ ] Customer list is cached
- [ ] Cache is invalidated on create/update/delete operations
- [ ] Redis unavailability degrades gracefully (falls back to DB, logs warning)

### ✓ Admin User Management (ADMIN only)

- [ ] Sidebar shows "Admin → Users" link only for ADMIN users
- [ ] Non-ADMIN users navigating to `/admin/users` are redirected to `/dashboard`
- [ ] ADMIN can view paginated user list
- [ ] ADMIN can search users by name/email
- [ ] ADMIN can filter by role and active status
- [ ] ADMIN can change a user's role (ADMIN/MANAGER/VIEWER)
- [ ] ADMIN can activate/deactivate a user
- [ ] Cannot deactivate the last active ADMIN (returns 409)
- [ ] Cannot remove ADMIN role from the last active ADMIN (returns 409)
- [ ] Cannot downgrade your own ADMIN role (returns 409)

---

## 3. API Endpoints

Run against a running backend:

```bash
BASE=http://localhost:8000/api/v1

# Health
curl $BASE/liveness | jq .alive                    # true
curl $BASE/readiness | jq .ready                   # true
curl $BASE/health | jq .status                     # "healthy"

# Unauthenticated access
curl -s -o /dev/null -w "%{http_code}" $BASE/customers   # 401
curl -s -o /dev/null -w "%{http_code}" $BASE/users       # 401

# Login
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password"}' | jq -r .access_token)

# Authenticated
curl -H "Authorization: Bearer $TOKEN" $BASE/customers | jq .total
curl -H "Authorization: Bearer $TOKEN" $BASE/dashboard/metrics | jq .total_customers
```

---

## 4. Tests

```bash
# Backend — all tests must pass, coverage ≥ 85%
docker compose exec backend pytest tests/ -v --cov=app --cov-fail-under=85

# Backend — unit tests only
docker compose exec backend pytest tests/unit/ -v

# Frontend — type check must pass
cd frontend && npm run type-check

# Frontend — lint must pass
cd frontend && npm run lint

# Frontend — Jest tests
cd frontend && npm test

# E2E — full stack must be running
npx playwright test
```

Expected results:
- [ ] All backend tests pass
- [ ] Backend coverage ≥ 85%
- [ ] All frontend Jest tests pass
- [ ] TypeScript type-check exits 0
- [ ] ESLint exits 0
- [ ] Playwright E2E tests pass (or are non-blocking on PRs)

---

## 5. Docker

```bash
# Build both images
docker build ./backend --target production -t csp-backend:test
docker build ./frontend --target production -t csp-frontend:test

# Start full stack
docker compose up --build -d
docker compose exec backend alembic upgrade head

# All containers healthy
docker compose ps
```

- [ ] Backend image builds successfully (production target)
- [ ] Frontend image builds successfully (production target)
- [ ] `docker compose ps` shows all 4 containers as healthy
- [ ] Frontend is accessible at http://localhost:3000
- [ ] Backend API docs accessible at http://localhost:8000/api/v1/docs

---

## 6. CI/CD

- [ ] `ci.yml` workflow passes on main branch
- [ ] `pr-validation.yml` fires on pull requests and all required jobs pass
- [ ] `main-build.yml` pushes Docker images to GHCR on merge to main
- [ ] `release.yml` creates a GitHub Release on `v*.*.*` tags
- [ ] No hardcoded secrets in any workflow file

---

## 7. Documentation

- [ ] `README.md` covers: features, tech stack, quick start, env vars, testing, CI/CD, deployment
- [ ] `docs/01-architecture-overview.md` — system diagram, component roles
- [ ] `docs/02-backend-architecture.md` — layer diagram, key modules
- [ ] `docs/03-frontend-architecture.md` — routing, state management, build output
- [ ] `docs/04-database-design.md` — ERD, table definitions, migration management
- [ ] `docs/05-authentication-flow.md` — JWT flow, RBAC, security notes
- [ ] `docs/06-redis-caching-strategy.md` — cache-aside pattern, TTLs, invalidation
- [ ] `docs/07-ai-insight-workflow.md` — Gemini integration, prompts, fallback
- [ ] `docs/08-dashboard-analytics-flow.md` — queries, caching, visualisation
- [ ] `docs/09-deployment-guide.md` — Docker, cloud options, migrations, backups
- [ ] `docs/10-troubleshooting-guide.md` — common issues and fixes

---

## 8. Security

- [ ] No default/weak `SECRET_KEY` in production `.env`
- [ ] All Docker containers run as non-root users
- [ ] Security headers present on both backend and frontend responses
- [ ] CORS is restricted to specific origins
- [ ] Rate limiting is active on auth endpoints
- [ ] No secrets in git history (`git log --all --full-history -- "*.env"` shows no real values)

---

## 9. Production Readiness

- [ ] `deployment/docker-compose.production.yml` reviewed and configured
- [ ] Nginx config in `deployment/nginx/nginx.conf` reviewed
- [ ] TLS certificate configured (real cert, not self-signed)
- [ ] Data directories mounted as bind volumes (not anonymous volumes)
- [ ] Redis maxmemory and eviction policy set
- [ ] PostgreSQL backup script configured
- [ ] Monitoring/alerting recommended setup documented

---

## Final Sign-off

| Area | Status | Notes |
|------|--------|-------|
| Authentication | ☐ | |
| Customer CRUD | ☐ | |
| Interaction CRUD | ☐ | |
| AI Insights | ☐ | |
| Dashboard | ☐ | |
| Redis Cache | ☐ | |
| Admin Users | ☐ | |
| Tests | ☐ | |
| Docker | ☐ | |
| CI/CD | ☐ | |
| Documentation | ☐ | |
| Security | ☐ | |

**Reviewer:** ___________________  **Date:** ___________________
