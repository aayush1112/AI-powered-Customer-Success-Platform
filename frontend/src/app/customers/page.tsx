"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";

import { PageHeader } from "@/components/layouts/PageHeader";
import { Button } from "@/components/ui/button";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/features/auth";
import {
  CustomerFilters,
  CustomerTable,
  DeleteCustomerDialog,
} from "@/features/customers";
import type { CustomerResponse, CustomerStatus } from "@/features/customers/types";
import {
  useDeleteCustomerMutation,
  useGetCustomersQuery,
} from "@/services/api/customersApi";

const PAGE_SIZE = 10;

export default function CustomersPage() {
  const { toast } = useToast();
  const { user, isAuthenticated, isInitialized } = useAuth();

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [status, setStatus] = useState<CustomerStatus | "">("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [deleteTarget, setDeleteTarget] = useState<CustomerResponse | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, status, sortBy, sortOrder]);

  const { data, isLoading, isFetching } = useGetCustomersQuery(
    {
      page,
      page_size: PAGE_SIZE,
      search: debouncedSearch || undefined,
      status: status || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
    { skip: !isInitialized || !isAuthenticated }
  );

  const [deleteCustomer, { isLoading: isDeleting }] = useDeleteCustomerMutation();

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    try {
      await deleteCustomer(deleteTarget.id).unwrap();
      toast({
        title: "Customer deleted",
        description: `${deleteTarget.company_name} has been archived.`,
      });
      setDeleteTarget(null);
    } catch {
      toast({
        variant: "destructive",
        title: "Delete failed",
        description: "Please try again.",
      });
    }
  }, [deleteTarget, deleteCustomer, toast]);

  const canEdit = user?.role === "ADMIN" || user?.role === "MANAGER";
  const canDelete = user?.role === "ADMIN";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        description={
          data
            ? `${data.total} account${data.total !== 1 ? "s" : ""} in your portfolio`
            : "Manage your customer accounts"
        }
        actions={
          user?.role !== "VIEWER" ? (
            <Button asChild>
              <Link href="/customers/new">
                <Plus className="mr-2 h-4 w-4" />
                Add Customer
              </Link>
            </Button>
          ) : undefined
        }
      />

      <CustomerFilters
        search={search}
        status={status}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSearchChange={setSearch}
        onStatusChange={setStatus}
        onSortByChange={setSortBy}
        onSortOrderChange={setSortOrder}
      />

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <>
          <div
            className={
              isFetching ? "opacity-60 transition-opacity duration-200" : ""
            }
          >
            <CustomerTable
              customers={data?.items ?? []}
              canEdit={canEdit}
              canDelete={canDelete}
              onDelete={setDeleteTarget}
            />
          </div>

          {data && data.pages > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    aria-disabled={page === 1}
                    className={
                      page === 1
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>
                <PaginationItem>
                  <span className="px-4 py-2 text-sm text-muted-foreground">
                    Page {page} of {data.pages}
                  </span>
                </PaginationItem>
                <PaginationItem>
                  <PaginationNext
                    onClick={() =>
                      setPage((p) => Math.min(data.pages, p + 1))
                    }
                    aria-disabled={page === data.pages}
                    className={
                      page === data.pages
                        ? "pointer-events-none opacity-50"
                        : "cursor-pointer"
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </>
      )}

      <DeleteCustomerDialog
        open={!!deleteTarget}
        companyName={deleteTarget?.company_name ?? ""}
        isLoading={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
