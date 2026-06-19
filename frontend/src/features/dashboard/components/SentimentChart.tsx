"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { SentimentBreakdown } from "../types";

const SLICES = [
  { key: "POSITIVE" as const, name: "Positive", color: "#22c55e" },
  { key: "NEUTRAL" as const, name: "Neutral", color: "#94a3b8" },
  { key: "NEGATIVE" as const, name: "Negative", color: "#ef4444" },
];

interface Props {
  data: SentimentBreakdown;
}

export function SentimentChart({ data }: Props) {
  const chartData = SLICES.map((s) => ({
    name: s.name,
    value: data[s.key],
    color: s.color,
  })).filter((d) => d.value > 0);

  const isEmpty = chartData.length === 0;
  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">AI Sentiment Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <div className="flex items-center justify-center h-[280px] text-sm text-muted-foreground italic">
            No AI insights generated yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={105}
                paddingAngle={3}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => [
                  `${value} (${((value / total) * 100).toFixed(1)}%)`,
                  "Insights",
                ]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
