"use client";

import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CustomerStatus } from "@/features/customers/types";

interface Props {
  search: string;
  status: CustomerStatus | "";
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSearchChange: (v: string) => void;
  onStatusChange: (v: CustomerStatus | "") => void;
  onSortByChange: (v: string) => void;
  onSortOrderChange: (v: "asc" | "desc") => void;
}

export function CustomerFilters({
  search,
  status,
  sortBy,
  sortOrder,
  onSearchChange,
  onStatusChange,
  onSortByChange,
  onSortOrderChange,
}: Props) {
  return (
    <div className="filter-bar flex flex-wrap items-center gap-3">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        <Input
          placeholder="Search company, contact, email…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      <Select
        value={status}
        onValueChange={(v) => onStatusChange(v as CustomerStatus | "")}
      >
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="All statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">All statuses</SelectItem>
          <SelectItem value="ACTIVE">Active</SelectItem>
          <SelectItem value="AT_RISK">At Risk</SelectItem>
          <SelectItem value="CHURNED">Churned</SelectItem>
          <SelectItem value="PROSPECT">Prospect</SelectItem>
        </SelectContent>
      </Select>

      <Select value={sortBy} onValueChange={onSortByChange}>
        <SelectTrigger className="w-[155px]">
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="created_at">Created Date</SelectItem>
          <SelectItem value="company_name">Company Name</SelectItem>
          <SelectItem value="status">Status</SelectItem>
          <SelectItem value="updated_at">Updated Date</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={sortOrder}
        onValueChange={(v) => onSortOrderChange(v as "asc" | "desc")}
      >
        <SelectTrigger className="w-[130px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="desc">Newest first</SelectItem>
          <SelectItem value="asc">Oldest first</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
