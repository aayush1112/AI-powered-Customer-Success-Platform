"use client"

import { Pencil } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { UserResponse } from "@/features/admin/types"
import { UserRoleBadge } from "./UserRoleBadge"

interface Props {
  users: UserResponse[]
  onEdit: (user: UserResponse) => void
}

export function UserTable({ users, onEdit }: Props) {
  if (users.length === 0) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-primary/20 bg-primary/5 text-center">
        <p className="text-sm font-medium text-foreground">No users found</p>
        <p className="text-xs text-muted-foreground max-w-xs">
          Try adjusting your search or filters.
        </p>
      </div>
    )
  }

  return (
    <div className="surface-elevated overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead className="hidden sm:table-cell">Email</TableHead>
            <TableHead>Role</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="hidden lg:table-cell">Joined</TableHead>
            <TableHead className="w-[50px]" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {users.map((user) => (
            <TableRow key={user.id}>
              <TableCell>
                <p className="font-medium">
                  {user.first_name} {user.last_name}
                </p>
                <p className="text-xs text-muted-foreground sm:hidden">{user.email}</p>
              </TableCell>
              <TableCell className="hidden sm:table-cell text-sm text-muted-foreground">
                {user.email}
              </TableCell>
              <TableCell>
                <UserRoleBadge role={user.role} />
              </TableCell>
              <TableCell>
                {user.is_active ? (
                  <Badge variant="outline" className="text-green-600 border-green-300">
                    Active
                  </Badge>
                ) : (
                  <Badge variant="secondary">Inactive</Badge>
                )}
              </TableCell>
              <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                {new Date(user.created_at).toLocaleDateString()}
              </TableCell>
              <TableCell>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onEdit(user)}
                  aria-label={`Edit ${user.first_name} ${user.last_name}`}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
