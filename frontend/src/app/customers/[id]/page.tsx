"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Pencil, Trash2 } from "lucide-react";

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
import {
  CustomerStatusBadge,
  DeleteCustomerDialog,
} from "@/features/customers";
import { CustomerInteractionTimeline } from "@/features/interactions";
import {
  useDeleteCustomerMutation,
  useGetCustomerQuery,
} from "@/services/api/customersApi";

export default function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const { user, isAuthenticated, isInitialized } = useAuth();
  const [showDelete, setShowDelete] = useState(false);

  const {
    data: customer,
    isLoading,
    error,
  } = useGetCustomerQuery(id, {
    skip: !isInitialized || !isAuthenticated,
  });

  const [deleteCustomer, { isLoading: isDeleting }] = useDeleteCustomerMutation();

  useEffect(() => {
    if (isInitialized && !isAuthenticated) router.replace("/login");
  }, [isInitialized, isAuthenticated, router]);

  useEffect(() => {
    if (error) {
      toast({
        variant: "destructive",
        title: "Not found",
        description: "Customer not found or has been deleted.",
      });
      router.replace("/customers");
    }
  }, [error, router, toast]);

  if (!isInitialized || isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <Skeleton className="h-10 w-56 rounded-xl" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
        </div>
        <Skeleton className="h-20 rounded-xl" />
      </div>
    );
  }

  if (!customer) return null;

  const canEdit = user?.role === "ADMIN" || user?.role === "MANAGER";
  const canDelete = user?.role === "ADMIN";

  async function handleDelete() {
    try {
      await deleteCustomer(customer!.id).unwrap();
      toast({
        title: "Customer deleted",
        description: `${customer!.company_name} has been archived.`,
      });
      router.replace("/customers");
    } catch {
      toast({
        variant: "destructive",
        title: "Delete failed",
        description: "Please try again.",
      });
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title={customer.company_name}
        description="Customer profile and interaction history"
        backHref="/customers"
        backLabel="Customers"
        actions={
          <div className="flex shrink-0 items-center gap-2">
            <CustomerStatusBadge status={customer.status} />
            {canEdit && (
              <Button asChild variant="outline" size="sm">
                <Link href={`/customers/${customer.id}/edit`}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit
                </Link>
              </Button>
            )}
            {canDelete && (
              <Button
                variant="outline"
                size="sm"
                className="text-destructive hover:bg-destructive hover:text-destructive-foreground border-destructive/50"
                onClick={() => setShowDelete(true)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Company Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Company Name
                </p>
                <p className="font-medium">{customer.company_name}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Industry
                </p>
                <p className="font-medium">{customer.industry ?? "—"}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Status
                </p>
                <CustomerStatusBadge status={customer.status} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Name
                </p>
                <p className="font-medium">{customer.contact_name}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Email
                </p>
                <a
                  href={`mailto:${customer.contact_email}`}
                  className="font-medium text-primary hover:underline"
                >
                  {customer.contact_email}
                </a>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Phone
                </p>
                <p className="font-medium">{customer.contact_phone ?? "—"}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="pt-5">
            <div className="flex flex-wrap gap-6 text-sm">
              <div>
                <p className="text-muted-foreground text-xs uppercase tracking-wide mb-0.5">
                  Added
                </p>
                <p className="font-medium">
                  {new Date(customer.created_at).toLocaleDateString("en-US", {
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
                  {new Date(customer.updated_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Interaction History</h2>
        </div>
        <CustomerInteractionTimeline
          customerId={customer.id}
          isAuthenticated={isAuthenticated}
        />
      </section>

      <DeleteCustomerDialog
        open={showDelete}
        companyName={customer.company_name}
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
      />
    </div>
  );
}
