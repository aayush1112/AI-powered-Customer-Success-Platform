import { Badge } from "@/components/ui/badge"
import type { UserRole } from "@/features/admin/types"

const ROLE_CONFIG: Record<
  UserRole,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  ADMIN: { label: "Admin", variant: "destructive" },
  MANAGER: { label: "Manager", variant: "default" },
  VIEWER: { label: "Viewer", variant: "secondary" },
}

interface Props {
  role: UserRole
}

export function UserRoleBadge({ role }: Props) {
  const config = ROLE_CONFIG[role] ?? { label: role, variant: "outline" as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}
