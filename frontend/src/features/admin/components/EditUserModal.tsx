"use client"

import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useAuth } from "@/features/auth"
import type { UserResponse, UserRole } from "@/features/admin/types"
import { useUpdateUserMutation } from "@/services/api/usersApi"

interface Props {
  user: UserResponse | null
  onClose: () => void
}

export function EditUserModal({ user, onClose }: Props) {
  const { user: currentUser } = useAuth()
  const [updateUser, { isLoading, error }] = useUpdateUserMutation()

  const [role, setRole] = useState<UserRole>("MANAGER")
  const [isActive, setIsActive] = useState<"true" | "false">("true")

  useEffect(() => {
    if (user) {
      setRole(user.role)
      setIsActive(user.is_active ? "true" : "false")
    }
  }, [user])

  const isSelf = user?.id === currentUser?.id

  const handleSave = async () => {
    if (!user) return
    try {
      await updateUser({
        id: user.id,
        data: { role, is_active: isActive === "true" },
      }).unwrap()
      onClose()
    } catch {
      // error rendered inline below
    }
  }

  const errorMessage =
    error && "data" in error
      ? ((error.data as { message?: string })?.message ?? "Update failed")
      : error
      ? "Update failed"
      : null

  return (
    <Dialog open={!!user} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>Edit User</DialogTitle>
        </DialogHeader>

        {user && (
          <div className="space-y-4 py-2">
            <div>
              <p className="text-sm font-medium">
                {user.first_name} {user.last_name}
              </p>
              <p className="text-xs text-muted-foreground">{user.email}</p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="edit-role">Role</Label>
              <Select
                value={role}
                onValueChange={(v) => setRole(v as UserRole)}
                disabled={isSelf}
              >
                <SelectTrigger id="edit-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ADMIN">Admin</SelectItem>
                  <SelectItem value="MANAGER">Manager</SelectItem>
                  <SelectItem value="VIEWER">Viewer</SelectItem>
                </SelectContent>
              </Select>
              {isSelf && (
                <p className="text-xs text-muted-foreground">
                  You cannot change your own role
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="edit-status">Status</Label>
              <Select value={isActive} onValueChange={(v) => setIsActive(v as "true" | "false")}>
                <SelectTrigger id="edit-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Active</SelectItem>
                  <SelectItem value="false">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {errorMessage && (
              <p className="text-sm text-destructive">{errorMessage}</p>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? "Saving…" : "Save changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
