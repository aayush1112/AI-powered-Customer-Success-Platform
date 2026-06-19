import { http, HttpResponse } from "msw";

const BASE = "http://localhost:8000/api/v1";

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authHandlers = [
  http.post(`${BASE}/auth/register`, () =>
    HttpResponse.json(
      { success: true, message: "User registered successfully" },
      { status: 201 }
    )
  ),

  http.post(`${BASE}/auth/login`, () =>
    HttpResponse.json(
      {
        access_token: "mock-access-token",
        refresh_token: "mock-refresh-token",
        token_type: "bearer",
      },
      { status: 200 }
    )
  ),

  http.get(`${BASE}/auth/me`, () =>
    HttpResponse.json(
      {
        id: "00000000-0000-0000-0000-000000000001",
        first_name: "Test",
        last_name: "User",
        email: "test@example.com",
        role: "MANAGER",
        is_active: true,
      },
      { status: 200 }
    )
  ),

  http.post(`${BASE}/auth/logout`, () =>
    HttpResponse.json({ success: true }, { status: 200 })
  ),
];

// ── Customers ─────────────────────────────────────────────────────────────────

export const customerHandlers = [
  http.get(`${BASE}/customers`, () =>
    HttpResponse.json(
      {
        items: [
          {
            id: "00000000-0000-0000-0000-000000000010",
            company_name: "Acme Corp",
            industry: "SaaS",
            contact_name: "Jane Doe",
            contact_email: "jane@acme.com",
            contact_phone: "+14155550100",
            status: "ACTIVE",
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-06-01T00:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 10,
        pages: 1,
      },
      { status: 200 }
    )
  ),

  http.post(`${BASE}/customers`, () =>
    HttpResponse.json(
      {
        success: true,
        data: {
          id: "00000000-0000-0000-0000-000000000011",
          company_name: "New Corp",
          industry: "Fintech",
          contact_name: "Bob Smith",
          contact_email: "bob@newcorp.com",
          contact_phone: null,
          status: "PROSPECT",
          created_at: "2026-06-18T00:00:00Z",
          updated_at: "2026-06-18T00:00:00Z",
        },
      },
      { status: 201 }
    )
  ),

  http.get(`${BASE}/customers/:id`, ({ params }) =>
    HttpResponse.json(
      {
        id: params.id,
        company_name: "Acme Corp",
        industry: "SaaS",
        contact_name: "Jane Doe",
        contact_email: "jane@acme.com",
        contact_phone: "+14155550100",
        status: "ACTIVE",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-06-01T00:00:00Z",
      },
      { status: 200 }
    )
  ),

  http.put(`${BASE}/customers/:id`, ({ params }) =>
    HttpResponse.json(
      {
        success: true,
        data: {
          id: params.id,
          company_name: "Updated Corp",
          industry: "SaaS",
          contact_name: "Jane Doe",
          contact_email: "jane@acme.com",
          contact_phone: null,
          status: "ACTIVE",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-18T00:00:00Z",
        },
      },
      { status: 200 }
    )
  ),

  http.delete(`${BASE}/customers/:id`, () => new HttpResponse(null, { status: 204 })),
];

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const dashboardHandlers = [
  http.get(`${BASE}/dashboard/metrics`, () =>
    HttpResponse.json(
      {
        total_customers: 42,
        active_customers: 30,
        at_risk_customers: 8,
        churned_customers: 4,
        total_interactions: 120,
        interactions_this_month: 15,
        positive_insights: 25,
        neutral_insights: 10,
        negative_insights: 5,
      },
      { status: 200 }
    )
  ),

  http.get(`${BASE}/dashboard/customer-status`, () =>
    HttpResponse.json(
      { ACTIVE: 30, AT_RISK: 8, CHURNED: 4, PROSPECT: 0 },
      { status: 200 }
    )
  ),

  http.get(`${BASE}/dashboard/interactions`, () =>
    HttpResponse.json(
      [
        { date: "2026-06-01", count: 5 },
        { date: "2026-06-08", count: 7 },
        { date: "2026-06-15", count: 3 },
      ],
      { status: 200 }
    )
  ),

  http.get(`${BASE}/dashboard/sentiment`, () =>
    HttpResponse.json(
      { POSITIVE: 25, NEUTRAL: 10, NEGATIVE: 5 },
      { status: 200 }
    )
  ),

  http.get(`${BASE}/dashboard/risks`, () =>
    HttpResponse.json([], { status: 200 })
  ),

  http.get(`${BASE}/dashboard/action-items`, () =>
    HttpResponse.json([], { status: 200 })
  ),

  http.get(`${BASE}/dashboard/recent-activity`, () =>
    HttpResponse.json([], { status: 200 })
  ),
];

// ── Insights ──────────────────────────────────────────────────────────────────

export const insightHandlers = [
  http.post(`${BASE}/insights/generate/:interactionId`, ({ params }) =>
    HttpResponse.json(
      {
        success: true,
        is_fallback: false,
        data: {
          id: "00000000-0000-0000-0000-000000000020",
          interaction_id: params.interactionId,
          summary: "Customer is satisfied and open to renewal.",
          sentiment: "POSITIVE",
          action_items: ["Send renewal docs"],
          risks: [],
          generated_at: "2026-06-18T12:00:00Z",
        },
      },
      { status: 201 }
    )
  ),

  http.get(`${BASE}/insights/:interactionId`, ({ params }) =>
    HttpResponse.json(
      {
        id: "00000000-0000-0000-0000-000000000020",
        interaction_id: params.interactionId,
        summary: "Customer is satisfied and open to renewal.",
        sentiment: "POSITIVE",
        action_items: ["Send renewal docs"],
        risks: [],
        generated_at: "2026-06-18T12:00:00Z",
      },
      { status: 200 }
    )
  ),
];

// ── Users ─────────────────────────────────────────────────────────────────────

const MOCK_USER_ADMIN = {
  id: "00000000-0000-0000-0000-000000000100",
  first_name: "Alice",
  last_name: "Admin",
  email: "alice@example.com",
  role: "ADMIN",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

const MOCK_USER_MANAGER = {
  id: "00000000-0000-0000-0000-000000000101",
  first_name: "Bob",
  last_name: "Manager",
  email: "bob@example.com",
  role: "MANAGER",
  is_active: true,
  created_at: "2026-02-01T00:00:00Z",
};

export const userHandlers = [
  http.get(`${BASE}/users`, () =>
    HttpResponse.json(
      {
        items: [MOCK_USER_ADMIN, MOCK_USER_MANAGER],
        total: 2,
        page: 1,
        page_size: 10,
        pages: 1,
      },
      { status: 200 }
    )
  ),

  http.get(`${BASE}/users/:id`, ({ params }) =>
    HttpResponse.json({ ...MOCK_USER_ADMIN, id: params.id }, { status: 200 })
  ),

  http.put(`${BASE}/users/:id`, async ({ params, request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...MOCK_USER_MANAGER, id: params.id, ...body },
      { status: 200 }
    );
  }),
];

// ── Combined ──────────────────────────────────────────────────────────────────

export const handlers = [
  ...authHandlers,
  ...customerHandlers,
  ...dashboardHandlers,
  ...insightHandlers,
  ...userHandlers,
];
