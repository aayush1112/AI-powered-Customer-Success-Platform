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
import type { CustomerFormData, CustomerResponse } from "@/features/customers/types";

const customerSchema = z.object({
  company_name: z.string().min(1, "Company name is required").max(255),
  industry: z.string().max(100).optional(),
  contact_name: z.string().min(1, "Contact name is required").max(200),
  contact_email: z.string().email("Please enter a valid email address"),
  contact_phone: z.string().max(20).optional(),
  status: z.enum(["ACTIVE", "AT_RISK", "CHURNED", "PROSPECT"]).optional(),
});

type FormValues = z.infer<typeof customerSchema>;

interface Props {
  defaultValues?: Partial<CustomerResponse>;
  onSubmit: (data: CustomerFormData) => Promise<void>;
  isLoading: boolean;
  mode: "create" | "edit";
}

export function CustomerForm({ defaultValues, onSubmit, isLoading, mode }: Props) {
  const form = useForm<FormValues>({
    resolver: zodResolver(customerSchema),
    defaultValues: {
      company_name: defaultValues?.company_name ?? "",
      industry: defaultValues?.industry ?? "",
      contact_name: defaultValues?.contact_name ?? "",
      contact_email: defaultValues?.contact_email ?? "",
      contact_phone: defaultValues?.contact_phone ?? "",
      status: defaultValues?.status,
    },
  });

  async function handleSubmit(values: FormValues) {
    const payload: CustomerFormData = {
      company_name: values.company_name,
      contact_name: values.contact_name,
      contact_email: values.contact_email,
      industry: values.industry || null,
      contact_phone: values.contact_phone || null,
      status: mode === "edit" ? values.status : undefined,
    };
    await onSubmit(payload);
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="company_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Company Name *</FormLabel>
                <FormControl>
                  <Input placeholder="Acme Inc" disabled={isLoading} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="industry"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Industry</FormLabel>
                <FormControl>
                  <Input
                    placeholder="SaaS, Healthcare…"
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
          name="contact_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Contact Name *</FormLabel>
              <FormControl>
                <Input placeholder="Jane Doe" disabled={isLoading} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="contact_email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Contact Email *</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder="jane@acme.com"
                    autoComplete="off"
                    disabled={isLoading}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="contact_phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Contact Phone</FormLabel>
                <FormControl>
                  <Input
                    placeholder="+1 415 555 0100"
                    disabled={isLoading}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {mode === "edit" && (
          <FormField
            control={form.control}
            name="status"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Status</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                  disabled={isLoading}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select status…" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="ACTIVE">Active</SelectItem>
                    <SelectItem value="AT_RISK">At Risk</SelectItem>
                    <SelectItem value="CHURNED">Churned</SelectItem>
                    <SelectItem value="PROSPECT">Prospect</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="submit" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {mode === "create" ? "Creating…" : "Saving…"}
              </>
            ) : mode === "create" ? (
              "Create Customer"
            ) : (
              "Save Changes"
            )}
          </Button>
        </div>
      </form>
    </Form>
  );
}
