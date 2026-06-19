"use client";

import Link from "next/link";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CustomerResponse } from "@/features/customers/types";
import { CustomerStatusBadge } from "./CustomerStatusBadge";

interface Props {
  customers: CustomerResponse[];
  canEdit: boolean;
  canDelete: boolean;
  onDelete: (customer: CustomerResponse) => void;
}

export function CustomerTable({ customers, canEdit, canDelete, onDelete }: Props) {
  if (customers.length === 0) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-primary/20 bg-primary/5 text-center">
        <p className="text-sm font-medium text-foreground">
          No customers found
        </p>
        <p className="text-xs text-muted-foreground max-w-xs">
          Try adjusting your search or filters, or add a new customer.
        </p>
      </div>
    );
  }

  return (
    <div className="surface-elevated overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Company</TableHead>
            <TableHead className="hidden sm:table-cell">Industry</TableHead>
            <TableHead>Contact</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="hidden lg:table-cell">Created</TableHead>
            <TableHead className="w-[50px]" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {customers.map((customer) => (
            <TableRow key={customer.id}>
              <TableCell>
                <Link
                  href={`/customers/${customer.id}`}
                  className="font-medium hover:underline"
                >
                  {customer.company_name}
                </Link>
                {customer.industry && (
                  <p className="text-xs text-muted-foreground sm:hidden">
                    {customer.industry}
                  </p>
                )}
              </TableCell>
              <TableCell className="hidden sm:table-cell text-muted-foreground text-sm">
                {customer.industry ?? "—"}
              </TableCell>
              <TableCell>
                <p className="text-sm">{customer.contact_name}</p>
                <p className="text-xs text-muted-foreground">
                  {customer.contact_email}
                </p>
              </TableCell>
              <TableCell>
                <CustomerStatusBadge status={customer.status} />
              </TableCell>
              <TableCell className="hidden lg:table-cell text-muted-foreground text-sm">
                {new Date(customer.created_at).toLocaleDateString()}
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreHorizontal className="h-4 w-4" />
                      <span className="sr-only">Open menu</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem asChild>
                      <Link href={`/customers/${customer.id}`}>
                        View details
                      </Link>
                    </DropdownMenuItem>
                    {canEdit && (
                      <DropdownMenuItem asChild>
                        <Link href={`/customers/${customer.id}/edit`}>
                          <Pencil className="mr-2 h-4 w-4" />
                          Edit
                        </Link>
                      </DropdownMenuItem>
                    )}
                    {canDelete && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => onDelete(customer)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
