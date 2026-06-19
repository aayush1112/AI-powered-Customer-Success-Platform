"use client";

import Link from "next/link";
import { MoreHorizontal, Pencil, Eye } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
import { InteractionTypeBadge } from "./InteractionTypeBadge";
import type { InteractionResponse } from "@/features/interactions/types";

interface Props {
  interactions: InteractionResponse[];
  canEdit: boolean;
}

export function InteractionTable({ interactions, canEdit }: Props) {
  if (interactions.length === 0) {
    return (
      <div className="rounded-lg border border-dashed py-12 text-center">
        <p className="text-muted-foreground text-sm">No interactions found.</p>
        <p className="text-muted-foreground text-xs mt-1">
          Try adjusting your filters or create a new interaction.
        </p>
      </div>
    );
  }

  return (
    <div className="surface-elevated overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead className="hidden md:table-cell">Customer</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="hidden sm:table-cell">Meeting Date</TableHead>
            <TableHead className="hidden lg:table-cell">Logged by</TableHead>
            <TableHead className="hidden xl:table-cell">Created</TableHead>
            <TableHead className="w-[60px]" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {interactions.map((interaction) => {
            const meetingDate = new Date(
              interaction.meeting_date
            ).toLocaleDateString("en-US", {
              year: "numeric",
              month: "short",
              day: "numeric",
            });
            const createdDate = new Date(
              interaction.created_at
            ).toLocaleDateString("en-US", {
              year: "numeric",
              month: "short",
              day: "numeric",
            });
            const createdBy = interaction.created_by_user
              ? `${interaction.created_by_user.first_name} ${interaction.created_by_user.last_name}`
              : "—";

            return (
              <TableRow key={interaction.id}>
                <TableCell className="font-medium max-w-[200px]">
                  <Link
                    href={`/interactions/${interaction.id}`}
                    className="hover:underline line-clamp-1"
                  >
                    {interaction.title}
                  </Link>
                </TableCell>
                <TableCell className="hidden md:table-cell text-muted-foreground">
                  <Link
                    href={`/customers/${interaction.customer.id}`}
                    className="hover:underline"
                  >
                    {interaction.customer.company_name}
                  </Link>
                </TableCell>
                <TableCell>
                  <InteractionTypeBadge type={interaction.interaction_type} />
                </TableCell>
                <TableCell className="hidden sm:table-cell text-muted-foreground text-sm">
                  {meetingDate}
                </TableCell>
                <TableCell className="hidden lg:table-cell text-muted-foreground text-sm">
                  {createdBy}
                </TableCell>
                <TableCell className="hidden xl:table-cell text-muted-foreground text-sm">
                  {createdDate}
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
                        <Link href={`/interactions/${interaction.id}`}>
                          <Eye className="mr-2 h-4 w-4" />
                          View details
                        </Link>
                      </DropdownMenuItem>
                      {canEdit && (
                        <DropdownMenuItem asChild>
                          <Link href={`/interactions/${interaction.id}/edit`}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit
                          </Link>
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
