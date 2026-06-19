"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Users,
  XCircle,
} from "lucide-react";

import { PageHeader } from "@/components/layouts/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/features/auth";
import {
  CustomerStatusChart,
  DashboardErrorState,
  DashboardSkeleton,
  InteractionTrendChart,
  InteractionTypeChart,
  MetricCard,
  RecentActivityFeed,
  SentimentChart,
  TopActionItemsChart,
  TopRisksChart,
} from "@/features/dashboard";
import type { DashboardPeriod } from "@/features/dashboard/types";
import {
  useGetActionItemAnalyticsQuery,
  useGetCustomerStatusAnalyticsQuery,
  useGetDashboardMetricsQuery,
  useGetInteractionAnalyticsQuery,
  useGetInteractionTypeAnalyticsQuery,
  useGetRecentActivityQuery,
  useGetRiskAnalyticsQuery,
  useGetSentimentAnalyticsQuery,
} from "@/services/api/dashboardApi";

const PERIODS: { value: DashboardPeriod; label: string; short: string }[] = [
  { value: "last_7_days", label: "Last 7 Days", short: "7 Days" },
  { value: "last_30_days", label: "Last 30 Days", short: "30 Days" },
  { value: "last_90_days", label: "Last 90 Days", short: "90 Days" },
  { value: "all_time", label: "All Time", short: "All Time" },
];

export default function DashboardPage() {
  const { user, isAuthenticated, isInitialized } = useAuth();
  const [period, setPeriod] = useState<DashboardPeriod>("last_30_days");

  const skip = !isInitialized || !isAuthenticated;

  const { data: metrics, isLoading: metricsLoading, error: metricsError, refetch: refetchMetrics } =
    useGetDashboardMetricsQuery(undefined, { skip });
  const { data: customerStatus, isLoading: statusLoading } =
    useGetCustomerStatusAnalyticsQuery(undefined, { skip });
  const { data: interactionTrends, isLoading: trendsLoading } =
    useGetInteractionAnalyticsQuery(period, { skip });
  const { data: interactionTypes, isLoading: typesLoading } =
    useGetInteractionTypeAnalyticsQuery(undefined, { skip });
  const { data: sentiment, isLoading: sentimentLoading } =
    useGetSentimentAnalyticsQuery(undefined, { skip });
  const { data: risks, isLoading: risksLoading } =
    useGetRiskAnalyticsQuery(undefined, { skip });
  const { data: actionItems, isLoading: actionItemsLoading } =
    useGetActionItemAnalyticsQuery(undefined, { skip });
  const { data: recentActivity, isLoading: activityLoading } =
    useGetRecentActivityQuery(undefined, { skip });

  if (!user) return null;

  const isAnyLoading =
    metricsLoading ||
    statusLoading ||
    trendsLoading ||
    typesLoading ||
    sentimentLoading ||
    risksLoading ||
    actionItemsLoading ||
    activityLoading;

  const selectedPeriodLabel =
    PERIODS.find((p) => p.value === period)?.label ?? "Last 30 Days";

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back, ${user.first_name}`}
        description="Your executive overview of customer health and team activity."
        actions={
          <div className="flex items-center gap-1 rounded-xl border bg-card p-1 shadow-sm">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  period === p.value
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                }`}
              >
                {p.short}
              </button>
            ))}
          </div>
        }
      />

      {isAnyLoading ? (
        <DashboardSkeleton />
      ) : metricsError ? (
        <DashboardErrorState
          message="Could not load dashboard metrics."
          onRetry={refetchMetrics}
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Total Customers"
              value={metrics?.total_customers ?? 0}
              description="All accounts"
              accent="primary"
              icon={<Users className="h-4 w-4" />}
            />
            <MetricCard
              title="Active Customers"
              value={metrics?.active_customers ?? 0}
              description="Healthy relationships"
              accent="success"
              icon={<CheckCircle2 className="h-4 w-4" />}
            />
            <MetricCard
              title="At Risk"
              value={metrics?.at_risk_customers ?? 0}
              description="Require attention"
              accent="warning"
              icon={<AlertTriangle className="h-4 w-4" />}
            />
            <MetricCard
              title="Churned"
              value={metrics?.churned_customers ?? 0}
              description="Lost accounts"
              accent="destructive"
              icon={<XCircle className="h-4 w-4" />}
            />
            <MetricCard
              title="Total Interactions"
              value={metrics?.total_interactions ?? 0}
              description="All time"
              accent="primary"
              icon={<TrendingUp className="h-4 w-4" />}
            />
            <MetricCard
              title="This Month"
              value={metrics?.interactions_this_month ?? 0}
              description="Interactions logged"
              accent="primary"
            />
            <MetricCard
              title="Positive Insights"
              value={metrics?.positive_insights ?? 0}
              description="AI-rated positive"
              accent="success"
            />
            <MetricCard
              title="Negative Insights"
              value={metrics?.negative_insights ?? 0}
              description="AI-rated negative"
              accent="destructive"
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {customerStatus ? (
              <CustomerStatusChart data={customerStatus} />
            ) : (
              <DashboardErrorState message="Could not load customer status data." />
            )}
            {interactionTrends ? (
              <InteractionTrendChart
                data={interactionTrends}
                periodLabel={selectedPeriodLabel}
              />
            ) : (
              <DashboardErrorState message="Could not load interaction trends." />
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {interactionTypes ? (
              <InteractionTypeChart data={interactionTypes} />
            ) : (
              <DashboardErrorState message="Could not load interaction type data." />
            )}
            {sentiment ? (
              <SentimentChart data={sentiment} />
            ) : (
              <DashboardErrorState message="Could not load sentiment data." />
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {risks ? (
              <TopRisksChart data={risks} />
            ) : (
              <DashboardErrorState message="Could not load risk data." />
            )}
            {actionItems ? (
              <TopActionItemsChart data={actionItems} />
            ) : (
              <DashboardErrorState message="Could not load action item data." />
            )}
          </div>

          {recentActivity ? (
            <RecentActivityFeed items={recentActivity} />
          ) : (
            <DashboardErrorState message="Could not load recent activity." />
          )}
        </>
      )}
    </div>
  );
}
