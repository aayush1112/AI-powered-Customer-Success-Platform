export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const API_TIMEOUT = 30_000;

export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  DASHBOARD: "/dashboard",
  CUSTOMERS: "/customers",
  INTERACTIONS: "/interactions",
  INSIGHTS: "/insights",
  SETTINGS: "/settings",
} as const;

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_SIZE: 20,
  MAX_SIZE: 100,
} as const;

export const CACHE_TAGS = {
  AUTH: "Auth",
  CUSTOMERS: "Customer",
  INTERACTIONS: "Interaction",
  DASHBOARD: "Dashboard",
  INSIGHTS: "Insight",
} as const;
