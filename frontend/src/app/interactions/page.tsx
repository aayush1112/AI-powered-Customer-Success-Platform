"use client";

import { useEffect, useState } from "react";
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
import { useAuth } from "@/features/auth";
import { InteractionFilters, InteractionTable } from "@/features/interactions";
import type { InteractionType } from "@/features/interactions/types";
import { useGetInteractionsQuery } from "@/services/api/interactionsApi";

const PAGE_SIZE = 10;

export default function InteractionsPage() {
  const { user, isAuthenticated, isInitialized } = useAuth();

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [customerIdFilter, setCustomerIdFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [sortBy, setSortBy] = useState("meeting_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [customerIdFilter, typeFilter, sortBy, sortOrder]);

  const { data, isLoading, isFetching } = useGetInteractionsQuery(
    {
      page,
      page_size: PAGE_SIZE,
      search: debouncedSearch || undefined,
      customer_id: customerIdFilter || undefined,
      interaction_type: (typeFilter as InteractionType) || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
    { skip: !isInitialized || !isAuthenticated }
  );

  if (!user) return null;

  const canEdit = user.role === "ADMIN" || user.role === "MANAGER";
  const totalPages = data?.pages ?? 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Interactions"
        description="Meetings, calls, emails, and QBRs with your customers"
        actions={
          canEdit ? (
            <Button asChild>
              <Link href="/interactions/new">
                <Plus className="mr-2 h-4 w-4" />
                Log Interaction
              </Link>
            </Button>
          ) : undefined
        }
      />

      <InteractionFilters
        search={search}
        onSearchChange={setSearch}
        customerIdFilter={customerIdFilter}
        onCustomerIdChange={setCustomerIdFilter}
        typeFilter={typeFilter}
        onTypeChange={setTypeFilter}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        sortOrder={sortOrder}
        onSortOrderChange={setSortOrder}
      />

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
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
            <InteractionTable
              interactions={data?.items ?? []}
              canEdit={canEdit}
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
                    onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
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
    </div>
  );
}
