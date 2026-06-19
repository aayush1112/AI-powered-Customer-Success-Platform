export type DashboardPeriod = "last_7_days" | "last_30_days" | "last_90_days" | "all_time";

export interface DashboardMetrics {
  total_customers: number;
  active_customers: number;
  at_risk_customers: number;
  churned_customers: number;
  total_interactions: number;
  interactions_this_month: number;
  positive_insights: number;
  neutral_insights: number;
  negative_insights: number;
}

export interface CustomerStatusBreakdown {
  ACTIVE: number;
  AT_RISK: number;
  CHURNED: number;
  PROSPECT: number;
}

export interface InteractionTrendPoint {
  date: string;
  count: number;
}

export interface InteractionTypeBreakdown {
  MEETING: number;
  CALL: number;
  EMAIL: number;
  QBR: number;
}

export interface SentimentBreakdown {
  POSITIVE: number;
  NEUTRAL: number;
  NEGATIVE: number;
}

export interface RiskItem {
  risk: string;
  count: number;
}

export interface ActionItem {
  action: string;
  count: number;
}

export interface RecentActivityItem {
  type: "customer" | "interaction" | "insight";
  title: string;
  subtitle: string | null;
  timestamp: string;
}
