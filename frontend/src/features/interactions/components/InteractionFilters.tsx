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
import type { InteractionType } from "@/features/interactions/types";
import { useGetCustomersQuery } from "@/services/api/customersApi";

interface Props {
  search: string;
  onSearchChange: (v: string) => void;
  customerIdFilter: string;
  onCustomerIdChange: (v: string) => void;
  typeFilter: string;
  onTypeChange: (v: string) => void;
  sortBy: string;
  onSortByChange: (v: string) => void;
  sortOrder: "asc" | "desc";
  onSortOrderChange: (v: "asc" | "desc") => void;
}

const INTERACTION_TYPES: { value: InteractionType; label: string }[] = [
  { value: "MEETING", label: "Meeting" },
  { value: "CALL", label: "Call" },
  { value: "EMAIL", label: "Email" },
  { value: "QBR", label: "QBR" },
];

export function InteractionFilters({
  search,
  onSearchChange,
  customerIdFilter,
  onCustomerIdChange,
  typeFilter,
  onTypeChange,
  sortBy,
  onSortByChange,
  sortOrder,
  onSortOrderChange,
}: Props) {
  const { data: customersData } = useGetCustomersQuery({
    page: 1,
    page_size: 100,
    sort_by: "company_name",
    sort_order: "asc",
  });

  return (
    <div className="filter-bar flex flex-wrap items-center gap-3">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search title or notes…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      <Select
        value={customerIdFilter || "__all__"}
        onValueChange={(v) => onCustomerIdChange(v === "__all__" ? "" : v)}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="All customers" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All customers</SelectItem>
          {customersData?.items.map((c) => (
            <SelectItem key={c.id} value={c.id}>
              {c.company_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={typeFilter || "__all__"}
        onValueChange={(v) => onTypeChange(v === "__all__" ? "" : v)}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="All types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All types</SelectItem>
          {INTERACTION_TYPES.map((t) => (
            <SelectItem key={t.value} value={t.value}>
              {t.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={sortBy} onValueChange={onSortByChange}>
        <SelectTrigger className="w-[160px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="meeting_date">Meeting Date</SelectItem>
          <SelectItem value="created_at">Created Date</SelectItem>
          <SelectItem value="title">Title</SelectItem>
        </SelectContent>
      </Select>

      <Select value={sortOrder} onValueChange={(v) => onSortOrderChange(v as "asc" | "desc")}>
        <SelectTrigger className="w-[140px]">
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
