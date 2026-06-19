"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { TimelineCard } from "./TimelineCard";
import { useGetCustomerTimelineQuery } from "@/services/api/interactionsApi";

interface Props {
  customerId: string;
  isAuthenticated: boolean;
}

export function CustomerInteractionTimeline({
  customerId,
  isAuthenticated,
}: Props) {
  const { data, isLoading, isError } = useGetCustomerTimelineQuery(customerId, {
    skip: !isAuthenticated,
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <p className="text-sm text-muted-foreground">
        Unable to load interaction history.
      </p>
    );
  }

  if (!data || data.total === 0) {
    return (
      <div className="rounded-lg border border-dashed p-6 text-center">
        <p className="text-sm text-muted-foreground">
          No interactions recorded yet.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        {data.total} interaction{data.total !== 1 ? "s" : ""} · most recent first
      </p>
      {data.interactions.map((interaction) => (
        <TimelineCard key={interaction.id} interaction={interaction} />
      ))}
    </div>
  );
}
