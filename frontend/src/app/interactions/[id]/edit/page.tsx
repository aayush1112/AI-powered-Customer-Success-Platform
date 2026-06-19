"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

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
import {
  useGetInteractionQuery,
  useUpdateInteractionMutation,
} from "@/services/api/interactionsApi";

export default function EditInteractionPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const { user, isAuthenticated, isInitialized } = useAuth();

  const { data: interaction, isLoading } = useGetInteractionQuery(id, {
    skip: !isInitialized || !isAuthenticated,
  });

  const [updateInteraction, { isLoading: isUpdating }] =
    useUpdateInteractionMutation();

  useEffect(() => {
    if (!isInitialized) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (user?.role === "VIEWER") {
      router.replace(`/interactions/${id}`);
    }
  }, [isInitialized, isAuthenticated, user, router, id]);

  if (!isInitialized || isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-10 w-48 rounded-xl" />
        <Skeleton className="h-[480px] w-full rounded-xl" />
      </div>
    );
  }

  if (!interaction) return null;

  async function handleSubmit(data: InteractionFormData) {
    try {
      await updateInteraction({
        id,
        data: {
          title: data.title,
          interaction_type: data.interaction_type,
          meeting_date: data.meeting_date,
          notes: data.notes,
        },
      }).unwrap();
      toast({
        title: "Interaction updated",
        description: "Changes saved successfully.",
      });
      router.push(`/interactions/${id}`);
    } catch (err: unknown) {
      const msg =
        (err as { data?: { detail?: string } })?.data?.detail ??
        "Failed to save changes. Please try again.";
      toast({ variant: "destructive", title: "Update failed", description: msg });
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Edit Interaction"
        description={`Update details for "${interaction.title}".`}
        backHref={`/interactions/${id}`}
        backLabel="Back to interaction"
      />

      <Card>
        <CardHeader>
          <CardTitle>Edit Interaction</CardTitle>
          <CardDescription>
            Update details for &ldquo;{interaction.title}&rdquo;.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <InteractionForm
            mode="edit"
            defaultValues={interaction}
            isLoading={isUpdating}
            onSubmit={handleSubmit}
          />
        </CardContent>
      </Card>
    </div>
  );
}
