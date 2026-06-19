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
import { CustomerForm } from "@/features/customers";
import type { CustomerFormData } from "@/features/customers/types";
import {
  useGetCustomerQuery,
  useUpdateCustomerMutation,
} from "@/services/api/customersApi";

export default function EditCustomerPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const { user, isAuthenticated, isInitialized } = useAuth();

  const { data: customer, isLoading } = useGetCustomerQuery(id, {
    skip: !isInitialized || !isAuthenticated,
  });

  const [updateCustomer, { isLoading: isUpdating }] = useUpdateCustomerMutation();

  useEffect(() => {
    if (!isInitialized) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (user?.role === "VIEWER") {
      router.replace(`/customers/${id}`);
    }
  }, [isInitialized, isAuthenticated, user, router, id]);

  if (!isInitialized || isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-10 w-48 rounded-xl" />
        <Skeleton className="h-[420px] w-full rounded-xl" />
      </div>
    );
  }

  if (!customer) return null;

  async function handleSubmit(data: CustomerFormData) {
    try {
      await updateCustomer({
        id,
        data: {
          company_name: data.company_name,
          contact_name: data.contact_name,
          contact_email: data.contact_email,
          industry: data.industry ?? undefined,
          contact_phone: data.contact_phone ?? undefined,
          status: data.status,
        },
      }).unwrap();
      toast({ title: "Customer updated", description: "Changes saved successfully." });
      router.push(`/customers/${id}`);
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
        title={`Edit ${customer.company_name}`}
        description="Update company and contact information."
        backHref={`/customers/${id}`}
        backLabel="Back to customer"
      />

      <Card>
        <CardHeader>
          <CardTitle>Edit Customer</CardTitle>
          <CardDescription>
            Update information for {customer.company_name}.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CustomerForm
            mode="edit"
            defaultValues={customer}
            isLoading={isUpdating}
            onSubmit={handleSubmit}
          />
        </CardContent>
      </Card>
    </div>
  );
}
