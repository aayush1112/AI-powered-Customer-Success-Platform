import { Badge } from "@/components/ui/badge";
import type { CustomerStatus } from "@/features/customers/types";

const STATUS_CONFIG: Record<
  CustomerStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" }
> = {
  ACTIVE: { label: "Active", variant: "success" },
  AT_RISK: { label: "At Risk", variant: "warning" },
  CHURNED: { label: "Churned", variant: "destructive" },
  PROSPECT: { label: "Prospect", variant: "default" },
};

interface Props {
  status: CustomerStatus;
}

export function CustomerStatusBadge({ status }: Props) {
  const config = STATUS_CONFIG[status] ?? { label: status, variant: "outline" as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
