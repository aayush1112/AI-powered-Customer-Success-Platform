"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Loader2, Pencil, RefreshCw, Sparkles } from "lucide-react";

import { PageHeader } from "@/components/layouts/PageHeader";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/features/auth";
import { InteractionTypeBadge } from "@/features/interactions";
import { AIInsightCard } from "@/features/insights";
import { useGetInteractionQuery } from "@/services/api/interactionsApi";
import {
  useGenerateInsightMutation,
  useGetInsightQuery,
  useRegenerateInsightMutation,
} from "@/services/api/insightsApi";

export default function InteractionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const { user, isAuthenticated, isInitialized } = useAuth();

  const {
    data: interaction,
    isLoading,
    error,
  } = useGetInteractionQuery(id, {
    skip: !isInitialized || !isAuthenticated,
  });

  const { data: insight, isLoading: isInsightLoading } = useGetInsightQuery(id, {
    skip: !isInitialized || !isAuthenticated,
  });

  const [generateInsight, { isLoading: isGenerating }] = useGenerateInsightMutation();
  const [regenerateInsight, { isLoading: isRegenerating }] = useRegenerateInsightMutation();

  useEffect(() => {
    if (isInitialized && !isAuthenticated) router.replace("/login");
  }, [isInitialized, isAuthenticated, router]);

  useEffect(() => {
    if (error) {
      toast({
        variant: "destructive",
        title: "Not found",
        description: "Interaction not found.",
      });
      router.replace("/interactions");
    }
  }, [error, router, toast]);

  if (!isInitialized || isLoading) {
    return (
      <div className="min-h-screen bg-background px-6 py-6 space-y-4">
        <Skeleton className="h-10 w-56" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (!interaction) return null;

  const canEdit = user?.role === "ADMIN" || user?.role === "MANAGER";
  const isAiWorking = isGenerating || isRegenerating;

  const meetingDate = new Date(interaction.meeting_date).toLocaleDateString(
    "en-US",
    {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
  const createdBy = interaction.created_by_user
    ? `${interaction.created_by_user.first_name} ${interaction.created_by_user.last_name}`
    : "—";

  async function handleGenerate() {
    try {
      const result = await generateInsight(id).unwrap();
      toast({
        title: result.is_fallback ? "AI unavailable" : "Insight generated",
        description: result.is_fallback
          ? "The AI service is temporarily unavailable. A placeholder has been saved."
          : "AI analysis complete.",
        variant: result.is_fallback ? "destructive" : "default",
      });
    } catch {
      toast({
        variant: "destructive",
        title: "Generation failed",
        description: "Could not generate insight. Please try again.",
      });
    }
  }

  async function handleRegenerate() {
    try {
      const result = await regenerateInsight(id).unwrap();
      toast({
        title: result.is_fallback ? "AI unavailable" : "Insight refreshed",
        description: result.is_fallback
          ? "The AI service is temporarily unavailable. A placeholder has been saved."
          : "AI analysis updated.",
        variant: result.is_fallback ? "destructive" : "default",
      });
    } catch {
      toast({
        variant: "destructive",
        title: "Regeneration failed",
        description: "Could not regenerate insight. Please try again.",
      });
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title={interaction.title}
        description="Interaction details and AI-generated insights"
        backHref="/interactions"
        backLabel="Interactions"
        actions={
          canEdit ? (
            <Button asChild variant="outline" size="sm">
              <Link href={`/interactions/${interaction.id}/edit`}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </Link>
            </Button>
          ) : undefined
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Interaction Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Customer
                </p>
                <Link
                  href={`/customers/${interaction.customer.id}`}
                  className="font-medium text-primary hover:underline"
                >
                  {interaction.customer.company_name}
                </Link>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Type
                </p>
                <InteractionTypeBadge type={interaction.interaction_type} />
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Meeting Date
                </p>
                <p className="font-medium">{meetingDate}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Record</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Logged By
                </p>
                <p className="font-medium">{createdBy}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Created
                </p>
                <p className="font-medium">
                  {new Date(interaction.created_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Last Updated
                </p>
                <p className="font-medium">
                  {new Date(interaction.updated_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Meeting notes ────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Meeting Notes</CardTitle>
          </CardHeader>
          <CardContent>
            {interaction.notes ? (
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {interaction.notes}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground italic">
                No notes recorded.
              </p>
            )}
          </CardContent>
        </Card>

        {/* ── AI Insight ───────────────────────────────────────────── */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold">AI Insight</h2>

            {canEdit && (
              <Button
                size="sm"
                variant={insight ? "outline" : "default"}
                disabled={isAiWorking}
                onClick={insight ? handleRegenerate : handleGenerate}
              >
                {isAiWorking ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating…
                  </>
                ) : insight ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Regenerate
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Insight
                  </>
                )}
              </Button>
            )}
          </div>

          {isInsightLoading || isAiWorking ? (
            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-3 w-48 mt-1" />
              </CardHeader>
              <CardContent className="space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-5/6" />
              </CardContent>
            </Card>
          ) : insight ? (
            <AIInsightCard insight={insight} />
          ) : (
            <div className="rounded-lg border-2 border-dashed p-6 text-center text-sm text-muted-foreground">
              {canEdit
                ? "No AI insight yet. Click Generate Insight to analyse the meeting notes."
                : "No AI insight has been generated for this interaction."}
            </div>
          )}
        </section>
    </div>
  );
}
