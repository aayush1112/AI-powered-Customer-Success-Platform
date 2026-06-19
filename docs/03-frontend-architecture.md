# Frontend Architecture

## Technology Stack

| Technology | Version | Role |
|-----------|---------|------|
| Next.js | 15.1 | App Router SSR/SSG framework |
| React | 19 | UI library |
| TypeScript | 5.7 | Type safety |
| Tailwind CSS | 3.4 | Utility-first styling |
| shadcn/ui | latest | Radix-based accessible component primitives |
| Redux Toolkit | 2.3 | Global state management |
| RTK Query | 2.3 | Server state + API cache |
| react-hook-form | 7.54 | Form state management |
| Zod | 3.24 | Schema validation (form + API contracts) |
| Recharts | 2.15 | Dashboard data visualisation |
| lucide-react | 0.468 | Icon library |
| next-themes | 0.4 | Dark/light mode |
| MSW | 2.6 | API mocking in tests |
| Jest + Testing Library | 29 | Unit + component tests |
| Playwright | latest | End-to-end tests |

---

## Application Structure

```
frontend/src/
├── app/                        Next.js App Router
│   ├── layout.tsx              Root layout (ThemeProvider, Redux store)
│   ├── page.tsx                Root redirect → /dashboard
│   ├── login/                  Public auth pages
│   ├── register/
│   ├── dashboard/
│   │   └── layout.tsx          Protected layout (AppShell wraps children)
│   ├── customers/
│   │   ├── layout.tsx
│   │   ├── page.tsx            Customer list
│   │   └── [id]/page.tsx       Customer detail + interactions + insights
│   ├── interactions/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   └── admin/
│       ├── layout.tsx          Admin-only layout
│       └── users/page.tsx      User management (ADMIN role only)
│
├── components/
│   ├── layouts/
│   │   ├── AppShell.tsx        Sidebar + Header + main content area
│   │   ├── Sidebar.tsx         Navigation (role-aware: Admin section for ADMIN)
│   │   └── Header.tsx          Top bar with user menu + theme toggle
│   ├── ui/                     shadcn/ui primitives (button, badge, dialog, …)
│   └── providers/              Redux store + theme provider wrappers
│
├── features/                   Feature-scoped modules
│   ├── auth/                   Login, Register, token management
│   ├── customers/              Customer list, form, detail components
│   ├── interactions/           Interaction list + form
│   ├── insights/               AI Insight display
│   └── admin/                  User management (types, components, exports)
│
└── services/
    └── api/
        ├── baseApi.ts          RTK Query base with auth headers + tag types
        ├── authApi.ts          login, register, logout, me, refresh
        ├── customersApi.ts     CRUD + pagination
        ├── interactionsApi.ts  CRUD + pagination
        ├── insightsApi.ts      generate, get
        ├── dashboardApi.ts     metrics, charts
        └── usersApi.ts         getUsers, getUser, updateUser (ADMIN)
```

---

## Routing and Authentication

### Edge Middleware (`middleware.ts`)
Runs on every navigation before the page renders. Checks for the `auth_status` cookie (set by the frontend on login, cleared on logout). Redirects:
- Unauthenticated users from `/dashboard`, `/customers`, `/interactions`, `/admin` → `/login`
- Already-authenticated users from `/login`, `/register` → `/dashboard`

This is a **UX guard only** — the actual security boundary is the backend JWT validation.

### Client-side Role Guard
Protected pages additionally call `useAuth()` and check `user?.role` after the session is initialised. Non-ADMIN users landing on `/admin/users` are immediately redirected to `/dashboard`.

### Layout Chain
```
app/layout.tsx          (HTML shell, providers)
  └── [section]/layout.tsx   (AppShell with Sidebar + Header)
        └── page.tsx           (Page content)
```

Every section (`dashboard`, `customers`, `interactions`, `admin`) has its own `layout.tsx` that wraps children in `AppShell`. This provides the consistent sidebar + header without duplicating markup.

---

## State Management

### Redux Toolkit
Used for global client state:
- `authSlice` — `{ user, accessToken, isAuthenticated, isInitialized }`
- Token storage in `localStorage` via `tokenStorage.ts`
- Hydrated from `localStorage` on app init via `useAuth()` hook

### RTK Query (server state)
All API interactions go through RTK Query endpoints defined in `services/api/*.ts`. Benefits:
- Automatic caching with tag-based invalidation
- Deduplication of concurrent requests
- Loading/error states without manual useState
- `skip` option to delay queries until auth is initialised

Tag types: `Customer`, `Interaction`, `Insight`, `Dashboard`, `User`

---

## Component Conventions

- All shared UI primitives live in `components/ui/` (shadcn/ui wrappers — never modified directly)
- Feature-specific components live inside `features/<feature>/components/`
- Barrel exports from `features/<feature>/index.ts`
- Forms use `react-hook-form` + `@hookform/resolvers/zod` for validation

---

## Testing Strategy

| Type | Tool | Location |
|------|------|----------|
| Component | Jest + Testing Library | `src/tests/features/` |
| Mock server | MSW v2 | `src/tests/mocks/handlers.ts` |
| E2E | Playwright (Chromium) | `e2e/*.spec.ts` |

**MSW handlers** intercept all `fetch` calls in Jest tests; no real network requests. The same MSW handlers are exportable for Storybook if added later.

**Playwright** runs against the full stack in CI: real backend, real PostgreSQL, real Redis, built frontend.

---

## Build Output

`next.config.ts` sets `output: "standalone"` — Next.js produces a self-contained node server at `.next/standalone/server.js` that includes only the packages used in production. The Docker image copies:
- `public/` — static assets
- `.next/standalone/` — server + bundled packages
- `.next/static/` — client-side JS/CSS chunks

This results in a significantly smaller production image (~150 MB vs ~800 MB for a full `node_modules` image).

---

## Security Headers (Frontend)

Set in `next.config.ts` via `headers()` for all routes:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
