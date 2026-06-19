"use client";

import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useGetCustomersQuery } from "@/services/api/customersApi";

interface Props {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function CustomerSelector({ value, onChange, disabled }: Props) {
  const { data, isLoading } = useGetCustomersQuery({
    page: 1,
    page_size: 100,
    sort_by: "company_name",
    sort_order: "asc",
  });

  if (isLoading) {
    return (
      <FormItem>
        <FormLabel>Customer *</FormLabel>
        <Skeleton className="h-10 w-full" />
      </FormItem>
    );
  }

  return (
    <FormItem>
      <FormLabel>Customer *</FormLabel>
      <Select onValueChange={onChange} value={value} disabled={disabled}>
        <FormControl>
          <SelectTrigger>
            <SelectValue placeholder="Select a customer…" />
          </SelectTrigger>
        </FormControl>
        <SelectContent>
          {data?.items.map((c) => (
            <SelectItem key={c.id} value={c.id}>
              {c.company_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <FormMessage />
    </FormItem>
  );
}
