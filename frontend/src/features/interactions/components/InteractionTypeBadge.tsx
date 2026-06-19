import { Badge } from "@/components/ui/badge";
import type { InteractionType } from "@/features/interactions/types";

const TYPE_CONFIG: Record<
  InteractionType,
  { label: string; variant: "default" | "secondary" | "outline" | "destructive" }
> = {
  MEETING: { label: "Meeting", variant: "default" },
  CALL: { label: "Call", variant: "secondary" },
  EMAIL: { label: "Email", variant: "outline" },
  QBR: { label: "QBR", variant: "destructive" },
};

interface Props {
  type: InteractionType;
}

export function InteractionTypeBadge({ type }: Props) {
  const config = TYPE_CONFIG[type] ?? { label: type, variant: "outline" as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
