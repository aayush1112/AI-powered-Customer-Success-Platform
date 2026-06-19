# Dashboard Analytics Flow

## Overview

The Dashboard module aggregates data from the `customers`, `interactions`, and `ai_insights` tables into summary metrics and chart-ready datasets. All dashboard endpoints are **read-only** and **cached in Redis** with a 5-minute TTL to avoid repeated expensive aggregate queries.

---

## Endpoints

| Endpoint | Response | Cache TTL |
|----------|----------|-----------|
| `GET /api/v1/dashboard/metrics` | Overall KPI summary | 5 min |
| `GET /api/v1/dashboard/customer-status` | Customers by status count | 5 min |
| `GET /api/v1/dashboard/interactions` | Weekly interaction volume (last 8 weeks) | 5 min |
| `GET /api/v1/dashboard/sentiment` | AI insight sentiment distribution | 5 min |
| `GET /api/v1/dashboard/risks` | High-risk customers list | 5 min |
| `GET /api/v1/dashboard/action-items` | Pending AI-recommended action items | 5 min |
| `GET /api/v1/dashboard/recent-activity` | Latest 10 interactions across all customers | 2 min |

---

## Data Flow

```
GET /api/v1/dashboard/metrics
  │
  ▼
DashboardService.get_metrics()
  │
  ├─► CacheService.get("csp:dashboard:metrics")
  │   ├─► HIT  → return cached DashboardMetrics
  │   └─► MISS → continue
  │
  ├─► DashboardRepository.get_metrics()
  │   ├─► COUNT(*) from customers                   (total)
  │   ├─► COUNT(*) WHERE status='ACTIVE'            (active)
  │   ├─► COUNT(*) WHERE status='AT_RISK'           (at_risk)
  │   ├─► COUNT(*) WHERE status='CHURNED'           (churned)
  │   ├─► COUNT(*) from interactions                (total)
  │   ├─► COUNT(*) WHERE occurred_at >= month_start (this_month)
  │   ├─► COUNT(*) from ai_insights WHERE sentiment='POSITIVE'
  │   ├─► COUNT(*) WHERE sentiment='NEUTRAL'
  │   └─► COUNT(*) WHERE sentiment='NEGATIVE'
  │
  ├─► Build DashboardMetrics response object
  │
  ├─► CacheService.set("csp:dashboard:metrics", data, ttl=300)
  │
  └─► Return DashboardMetrics
```

---

## Query Details

### `customer-status`
```sql
SELECT status, COUNT(*) AS count
FROM customers
GROUP BY status
```
Returns: `{ "ACTIVE": 30, "AT_RISK": 8, "CHURNED": 4, "PROSPECT": 5 }`

### `interactions` (weekly volume)
```sql
SELECT
    date_trunc('week', occurred_at) AS week,
    COUNT(*) AS count
FROM interactions
WHERE occurred_at >= NOW() - INTERVAL '8 weeks'
GROUP BY week
ORDER BY week
```

### `sentiment`
```sql
SELECT sentiment, COUNT(*) AS count
FROM ai_insights
GROUP BY sentiment
```

### `risks`
```sql
SELECT c.id, c.company_name, c.status, i.summary, i.risks
FROM customers c
JOIN interactions intr ON intr.customer_id = c.id
JOIN ai_insights i ON i.interaction_id = intr.id
WHERE c.status = 'AT_RISK'
  AND jsonb_array_length(i.risks) > 0
ORDER BY c.company_name
LIMIT 10
```

---

## Frontend Visualisation

The dashboard page (`app/dashboard/page.tsx`) uses **Recharts** for all charts:

| Chart | Type | Data Source |
|-------|------|-------------|
| Customer Status | Donut / Pie | `customer-status` |
| Interaction Volume | Area / Bar | `interactions` |
| Sentiment | Pie / Radial | `sentiment` |
| KPI Cards | Static cards | `metrics` |
| At-Risk Customers | Table | `risks` |
| Action Items | Checklist | `action-items` |
| Recent Activity | Timeline list | `recent-activity` |

All charts load independently via separate RTK Query hooks, so a slow or failed chart does not block the rest of the page from rendering.

---

## Cache Invalidation

Dashboard caches are invalidated when:
- A new insight is generated (sentiment counts change)
- A customer's status changes (customer-status changes)

Invalidation is performed by deleting all keys matching `csp:dashboard:*` pattern after the relevant write operation completes.

---

## Access Control

All dashboard endpoints require an authenticated user. No role restriction beyond authentication — all roles (ADMIN, MANAGER, VIEWER) can view the dashboard. This is enforced by `get_current_user()` dependency (no `require_role` constraint).
