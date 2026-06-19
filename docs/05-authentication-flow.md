# Authentication Flow

## Overview

CSP uses a **stateless dual-token JWT** strategy:
- **Access token** — short-lived (15 min); sent as `Authorization: Bearer <token>` on every API request
- **Refresh token** — long-lived (7 days); used only to obtain new access tokens; stored alongside the access token in `localStorage`

Password hashing uses **bcrypt** with per-user salt. No plaintext passwords are ever stored or logged.

---

## Token Claims

Both tokens share the following claim structure:

```json
{
  "sub": "<user_uuid>",
  "email": "user@example.com",
  "role": "MANAGER",
  "type": "access",        // or "refresh"
  "iat": 1719000000,
  "exp": 1719000900
}
```

The `type` claim prevents token substitution attacks (using a refresh token as an access token or vice versa).

---

## Registration Flow

```
POST /api/v1/auth/register
  Body: { first_name, last_name, email, password }

1. Validate request body (Pydantic)
2. Check email uniqueness → 409 if duplicate
3. Hash password with bcrypt
4. Create User record (role=VIEWER, is_active=True)
5. Persist to PostgreSQL
6. Return { success: true, message: "..." }
```

No token is issued at registration — the user must log in separately.

---

## Login Flow

```
POST /api/v1/auth/login
  Body: { email, password }

1. Look up User by email → 401 if not found
2. Check is_active → 403 if deactivated
3. verify_password(plain, hashed) → 401 if mismatch
4. create_access_token({ sub, email, role }) → 15 min
5. create_refresh_token({ sub, email, role }) → 7 days
6. Return { access_token, refresh_token, token_type: "bearer" }
```

**Frontend response handling:**
- Stores `access_token` and `refresh_token` in `localStorage` via `tokenStorage.ts`
- Sets `auth_status=1` cookie (non-sensitive flag for Edge Middleware)
- Dispatches `setCredentials({ user, accessToken })` to Redux `authSlice`

---

## Authenticated Request Flow

```
GET /api/v1/customers (with Bearer token)

1. LoggingMiddleware assigns request_id
2. CORSMiddleware checks Origin header
3. FastAPI dependency: get_current_user()
   a. Extract Authorization header → decode JWT
   b. Validate exp, iat, type == "access"
   c. Load User from DB by sub (UUID)
   d. Verify user.is_active → 401 if deactivated
4. require_role(UserRole.MANAGER, UserRole.ADMIN)
   a. Check user.role in allowed_roles → 403 if not
5. Service / Repository execute query
6. Return 200 with JSON payload
```

---

## Token Refresh Flow

```
POST /api/v1/auth/refresh
  Body: { refresh_token: "<token>" }

1. Decode refresh_token
2. Validate type == "refresh" and exp not elapsed
3. Load User from DB → 401 if not found or inactive
4. Issue new access_token (15 min)
5. Return { access_token, token_type: "bearer" }
```

**Frontend:** RTK Query `baseQuery` wrapper automatically calls this endpoint when a request returns 401, then replays the failed request with the new token. This is transparent to all feature-level API calls.

---

## Logout Flow

```
POST /api/v1/auth/logout
  (authenticated)

1. Log the logout event via structlog
2. Return { success: true }
```

**Frontend on logout:**
- Clears `localStorage` tokens via `tokenStorage.clearTokens()`
- Deletes `auth_status` cookie
- Dispatches `clearCredentials()` to Redux (clears user + token)
- Redirects to `/login`

**Note on token revocation:** The current implementation is stateless — there is no server-side token blacklist. The access token remains valid until its 15-minute TTL expires. This is a deliberate trade-off: it simplifies the implementation and the short TTL limits exposure. For stricter revocation, a Redis-backed blacklist can be added without changing the authentication flow.

---

## Role-Based Access Control

| Role | Capabilities |
|------|-------------|
| `ADMIN` | Full access: all modules + user management |
| `MANAGER` | Customers, Interactions, Insights, Dashboard (read + write) |
| `VIEWER` | Customers, Interactions, Insights, Dashboard (read only) — *future scope* |

RBAC is enforced at three layers:
1. **Frontend Sidebar** — Admin section hidden for non-ADMIN users
2. **Frontend Page** — `user?.role !== "ADMIN"` → redirect to `/dashboard`
3. **Backend** — `require_role(UserRole.ADMIN)` dependency on all `/users/*` endpoints

---

## Security Notes

| Concern | Implementation |
|---------|---------------|
| Password storage | bcrypt with random salt; cost factor ≥ 12 |
| Secret rotation | Change `SECRET_KEY` → all existing tokens become invalid immediately |
| Token expiry | Access: 15 min; Refresh: 7 days |
| Token type claim | Prevents refresh token used as access token |
| Brute-force | SlowAPI rate limit on `/auth/login` and `/auth/register` |
| Transport | HTTPS enforced in production via Nginx + HSTS header |
| Inactive users | `is_active=False` → 401/403 even with valid token |
