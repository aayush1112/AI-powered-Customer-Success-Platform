import { Building2, MessageSquare, Sparkles } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { RecentActivityItem } from "../types";

const TYPE_CONFIG = {
  customer: {
    icon: Building2,
    iconClass: "text-blue-500",
    bgClass: "bg-blue-50",
  },
  interaction: {
    icon: MessageSquare,
    iconClass: "text-green-500",
    bgClass: "bg-green-50",
  },
  insight: {
    icon: Sparkles,
    iconClass: "text-purple-500",
    bgClass: "bg-purple-50",
  },
} as const;

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface Props {
  items: RecentActivityItem[];
}

export function RecentActivityFeed({ items }: Props) {
  if (items.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8 italic">
            No recent activity yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {items.map((item, i) => {
          const cfg = TYPE_CONFIG[item.type];
          const Icon = cfg.icon;
          return (
            <div
              key={i}
              className="flex items-start gap-3 rounded-lg px-2 py-2 hover:bg-muted/50 transition-colors"
            >
              <div
                className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${cfg.bgClass}`}
              >
                <Icon className={`h-4 w-4 ${cfg.iconClass}`} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate leading-tight">
                  {item.title}
                </p>
                {item.subtitle && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {item.subtitle}
                  </p>
                )}
              </div>
              <time className="shrink-0 text-xs text-muted-foreground whitespace-nowrap">
                {formatTimestamp(item.timestamp)}
              </time>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
