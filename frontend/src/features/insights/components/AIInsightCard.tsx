import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { AIInsightResponse } from "../types";
import { SentimentBadge } from "./SentimentBadge";

interface Props {
  insight: AIInsightResponse;
}

export function AIInsightCard({ insight }: Props) {
  const generatedAt = new Date(insight.generated_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-base">AI Analysis</CardTitle>
          <SentimentBadge sentiment={insight.sentiment} />
        </div>
        <CardDescription>Generated {generatedAt}</CardDescription>
      </CardHeader>

      <CardContent className="space-y-5 text-sm">
        {/* Summary */}
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-1.5">
            Summary
          </p>
          <p className="leading-relaxed text-foreground">{insight.summary}</p>
        </div>

        {/* Action Items */}
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-1.5">
            Action Items
          </p>
          {insight.action_items.length > 0 ? (
            <ul className="space-y-1">
              {insight.action_items.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground italic">None identified.</p>
          )}
        </div>

        {/* Risks */}
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-1.5">
            Risks
          </p>
          {insight.risks.length > 0 ? (
            <ul className="space-y-1">
              {insight.risks.map((risk, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-destructive" />
                  <span className="text-destructive/90">{risk}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground italic">None identified.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
