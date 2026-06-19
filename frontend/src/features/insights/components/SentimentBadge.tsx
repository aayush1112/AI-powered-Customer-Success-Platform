import { Badge } from "@/components/ui/badge";
import type { SentimentType } from "../types";

interface Props {
  sentiment: SentimentType;
}

const CONFIG: Record<SentimentType, { label: string; className: string }> = {
  POSITIVE: {
    label: "Positive",
    className: "bg-green-100 text-green-800 border-green-200 hover:bg-green-100",
  },
  NEUTRAL: {
    label: "Neutral",
    className: "bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-100",
  },
  NEGATIVE: {
    label: "Negative",
    className: "bg-red-100 text-red-800 border-red-200 hover:bg-red-100",
  },
};

export function SentimentBadge({ sentiment }: Props) {
  const { label, className } = CONFIG[sentiment] ?? CONFIG.NEUTRAL;
  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  );
}
