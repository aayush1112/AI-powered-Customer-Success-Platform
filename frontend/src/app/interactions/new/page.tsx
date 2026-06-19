"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/layouts/PageHeader";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/features/auth";
import { InteractionForm } from "@/features/interactions";
import type { InteractionFormData } from "@/features/interactions/types";
import { useCreateInteractionMutation } from "@/services/api/interactionsApi";

export default function NewInteractionPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { user, isAuthenticated, isInitialized } = useAuth();
  const [createInteraction, { isLoading }] = useCreateInteractionMutation();

  useEffect(() => {
    if (!isInitialized) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (user?.role === "VIEWER") {
      router.replace("/interactions");
    }
  }, [isInitialized, isAuthenticated, user, router]);

  if (!isInitialized) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-[480px] w-full rounded-xl" />
      </div>
    );
  }

  if (!user || user.role === "VIEWER") return null;

  async function handleSubmit(data: InteractionFormData) {
    try {
      const result = await createInteraction({
        customer_id: data.customer_id,
        title: data.title,
        interaction_type: data.interaction_type,
        meeting_date: data.meeting_date,
        notes: data.notes,
      }).unwrap();
      toast({
        title: "Interaction logged",
        description: `"${data.title}" has been recorded.`,
      });
      router.push(`/interactions/${result.data.id}`);
    } catch (err: unknown) {
      const msg =
        (err as { data?: { detail?: string } })?.data?.detail ??
        "Failed to create interaction. Please try again.";
      toast({ variant: "destructive", title: "Create failed", description: msg });
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Log Interaction"
        description="Record a meeting, call, email, or QBR with a customer."
        backHref="/interactions"
        backLabel="Interactions"
      />

      <Card>
        <CardHeader>
          <CardTitle>New Interaction</CardTitle>
          <CardDescription>
            Capture the key details from your customer touchpoint.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <InteractionForm
            mode="create"
            isLoading={isLoading}
            onSubmit={handleSubmit}
          />
        </CardContent>
      </Card>
    </div>
  );
}
