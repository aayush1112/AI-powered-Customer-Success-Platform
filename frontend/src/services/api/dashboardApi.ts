import { baseApi } from "./baseApi";
import type {
  ActionItem,
  CustomerStatusBreakdown,
  DashboardMetrics,
  DashboardPeriod,
  InteractionTrendPoint,
  InteractionTypeBreakdown,
  RecentActivityItem,
  RiskItem,
  SentimentBreakdown,
} from "@/features/dashboard/types";

export const dashboardApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDashboardMetrics: builder.query<DashboardMetrics, void>({
      query: () => "/dashboard/metrics",
      providesTags: [{ type: "Dashboard", id: "metrics" }],
    }),

    getCustomerStatusAnalytics: builder.query<CustomerStatusBreakdown, void>({
      query: () => "/dashboard/customer-status",
      providesTags: [{ type: "Dashboard", id: "customer-status" }],
    }),

    getInteractionAnalytics: builder.query<InteractionTrendPoint[], DashboardPeriod>({
      query: (period) => ({
        url: "/dashboard/interactions",
        params: { period },
      }),
      providesTags: (_r, _e, period) => [{ type: "Dashboard", id: `interactions-${period}` }],
    }),

    getInteractionTypeAnalytics: builder.query<InteractionTypeBreakdown, void>({
      query: () => "/dashboard/interaction-types",
      providesTags: [{ type: "Dashboard", id: "interaction-types" }],
    }),

    getSentimentAnalytics: builder.query<SentimentBreakdown, void>({
      query: () => "/dashboard/sentiment",
      providesTags: [{ type: "Dashboard", id: "sentiment" }],
    }),

    getRiskAnalytics: builder.query<RiskItem[], void>({
      query: () => "/dashboard/risks",
      providesTags: [{ type: "Dashboard", id: "risks" }],
    }),

    getActionItemAnalytics: builder.query<ActionItem[], void>({
      query: () => "/dashboard/action-items",
      providesTags: [{ type: "Dashboard", id: "action-items" }],
    }),

    getRecentActivity: builder.query<RecentActivityItem[], void>({
      query: () => "/dashboard/recent-activity",
      providesTags: [{ type: "Dashboard", id: "recent-activity" }],
    }),
  }),
});

export const {
  useGetDashboardMetricsQuery,
  useGetCustomerStatusAnalyticsQuery,
  useGetInteractionAnalyticsQuery,
  useGetInteractionTypeAnalyticsQuery,
  useGetSentimentAnalyticsQuery,
  useGetRiskAnalyticsQuery,
  useGetActionItemAnalyticsQuery,
  useGetRecentActivityQuery,
} = dashboardApi;
