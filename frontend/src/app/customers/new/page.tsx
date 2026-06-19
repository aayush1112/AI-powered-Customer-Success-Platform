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
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/features/auth";
import { CustomerForm } from "@/features/customers";
import type { CustomerFormData } from "@/features/customers/types";
import { useCreateCustomerMutation } from "@/services/api/customersApi";

export default function NewCustomerPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { user, isAuthenticated, isInitialized } = useAuth();
  const [createCustomer, { isLoading }] = useCreateCustomerMutation();

  useEffect(() => {
    if (!isInitialized) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (user?.role === "VIEWER") {
      router.replace("/customers");
    }
  }, [isInitialized, isAuthenticated, user, router]);

  async function handleSubmit(data: CustomerFormData) {
    try {
      const result = await createCustomer({
        company_name: data.company_name,
        contact_name: data.contact_name,
        contact_email: data.contact_email,
        industry: data.industry ?? undefined,
        contact_phone: data.contact_phone ?? undefined,
      }).unwrap();
      toast({
        title: "Customer created",
        description: `${result.data.company_name} has been added.`,
      });
      router.push(`/customers/${result.data.id}`);
    } catch (err: unknown) {
      const msg =
        (err as { data?: { detail?: string } })?.data?.detail ??
        "Failed to create customer. Please try again.";
      toast({ variant: "destructive", title: "Creation failed", description: msg });
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="New Customer"
        description="Add a new company to your customer portfolio."
        backHref="/customers"
        backLabel="Customers"
      />

      <Card>
        <CardHeader>
          <CardTitle>Customer Details</CardTitle>
          <CardDescription>
            Fill in the company and primary contact information.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CustomerForm mode="create" isLoading={isLoading} onSubmit={handleSubmit} />
        </CardContent>
      </Card>
    </div>
  );
}
