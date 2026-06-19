"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { CustomerSelector } from "./CustomerSelector";
import type { InteractionFormData, InteractionResponse } from "@/features/interactions/types";

const interactionSchema = z.object({
  customer_id: z.string().min(1, "Customer is required"),
  title: z.string().min(3, "Title must be at least 3 characters").max(255),
  interaction_type: z.enum(["MEETING", "CALL", "EMAIL", "QBR"], {
    required_error: "Interaction type is required",
  }),
  meeting_date: z.string().min(1, "Meeting date is required"),
  notes: z
    .string()
    .min(10, "Notes must be at least 10 characters")
    .max(10000, "Notes must be 10,000 characters or fewer"),
});

type FormValues = z.infer<typeof interactionSchema>;

function toDateTimeLocal(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

interface Props {
  defaultValues?: Partial<InteractionResponse>;
  onSubmit: (data: InteractionFormData) => Promise<void>;
  isLoading: boolean;
  mode: "create" | "edit";
}

export function InteractionForm({ defaultValues, onSubmit, isLoading, mode }: Props) {
  const form = useForm<FormValues>({
    resolver: zodResolver(interactionSchema),
    defaultValues: {
      customer_id: defaultValues?.customer_id ?? "",
      title: defaultValues?.title ?? "",
      interaction_type: defaultValues?.interaction_type,
      meeting_date: defaultValues?.meeting_date
        ? toDateTimeLocal(defaultValues.meeting_date)
        : "",
      notes: defaultValues?.notes ?? "",
    },
  });

  async function handleSubmit(values: FormValues) {
    const payload: InteractionFormData = {
      customer_id: values.customer_id,
      title: values.title,
      interaction_type: values.interaction_type,
      meeting_date: new Date(values.meeting_date).toISOString(),
      notes: values.notes,
    };
    await onSubmit(payload);
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-5">
        <FormField
          control={form.control}
          name="customer_id"
          render={({ field }) => (
            <CustomerSelector
              value={field.value}
              onChange={field.onChange}
              disabled={isLoading}
            />
          )}
        />

        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Title *</FormLabel>
              <FormControl>
                <Input
                  placeholder="Q1 Business Review"
                  disabled={isLoading}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="interaction_type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Type *</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                  disabled={isLoading}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type…" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="MEETING">Meeting</SelectItem>
                    <SelectItem value="CALL">Call</SelectItem>
                    <SelectItem value="EMAIL">Email</SelectItem>
                    <SelectItem value="QBR">QBR</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="meeting_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Meeting Date *</FormLabel>
                <FormControl>
                  <Input
                    type="datetime-local"
                    disabled={isLoading}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes *</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Describe what was discussed, action items, and outcomes…"
                  rows={6}
                  disabled={isLoading}
                  className="resize-y"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-2 pt-1">
          <Button type="submit" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {mode === "create" ? "Creating…" : "Saving…"}
              </>
            ) : mode === "create" ? (
              "Log Interaction"
            ) : (
              "Save Changes"
            )}
          </Button>
        </div>
      </form>
    </Form>
  );
}
