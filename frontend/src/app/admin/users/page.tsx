"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { PageHeader } from "@/components/layouts/PageHeader"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useAuth } from "@/features/auth"
import { EditUserModal, UserTable } from "@/features/admin"
import type { UserResponse, UserRole } from "@/features/admin/types"
import { useGetUsersQuery } from "@/services/api/usersApi"

const PAGE_SIZE = 10

export default function AdminUsersPage() {
  const router = useRouter()
  const { user, isAuthenticated, isInitialized } = useAuth()

  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState<UserRole | "">("")
  const [isActiveFilter, setIsActiveFilter] = useState<"" | "true" | "false">("")
  const [page, setPage] = useState(1)
  const [editTarget, setEditTarget] = useState<UserResponse | null>(null)

  // Redirect non-admin users
  useEffect(() => {
    if (isInitialized && (!isAuthenticated || user?.role !== "ADMIN")) {
      router.replace("/dashboard")
    }
  }, [isInitialized, isAuthenticated, user, router])

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400)
    return () => clearTimeout(t)
  }, [search])

  // Reset to page 1 on filter changes
  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, roleFilter, isActiveFilter])

  const isAdmin = isInitialized && isAuthenticated && user?.role === "ADMIN"

  const { data, isLoading, isFetching } = useGetUsersQuery(
    {
      page,
      page_size: PAGE_SIZE,
      search: debouncedSearch || undefined,
      role: roleFilter || undefined,
      is_active: isActiveFilter === "" ? undefined : isActiveFilter === "true",
    },
    { skip: !isAdmin }
  )

  if (!isAdmin && isInitialized) return null

  return (
    <div className="space-y-6">
      <PageHeader
        title="User Management"
        description={
          data
            ? `${data.total} user${data.total !== 1 ? "s" : ""} in your platform`
            : "Manage platform users and roles"
        }
      />

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:max-w-xs"
        />
        <Select
          value={roleFilter}
          onValueChange={(v) => setRoleFilter(v as UserRole | "")}
        >
          <SelectTrigger className="sm:w-[160px]">
            <SelectValue placeholder="All roles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All roles</SelectItem>
            <SelectItem value="ADMIN">Admin</SelectItem>
            <SelectItem value="MANAGER">Manager</SelectItem>
            <SelectItem value="VIEWER">Viewer</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={isActiveFilter}
          onValueChange={(v) => setIsActiveFilter(v as "" | "true" | "false")}
        >
          <SelectTrigger className="sm:w-[160px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All statuses</SelectItem>
            <SelectItem value="true">Active</SelectItem>
            <SelectItem value="false">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <>
          <div className={isFetching ? "opacity-60 transition-opacity duration-200" : ""}>
            <UserTable users={data?.items ?? []} onEdit={setEditTarget} />
          </div>

          {data && data.pages > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    aria-disabled={page === 1}
                    className={page === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
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
                      page === data.pages ? "pointer-events-none opacity-50" : "cursor-pointer"
                    }
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </>
      )}

      <EditUserModal user={editTarget} onClose={() => setEditTarget(null)} />
    </div>
  )
}
