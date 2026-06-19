"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { InteractionTypeBreakdown } from "../types";

const TYPE_COLORS: Record<string, string> = {
  Meeting: "#3b82f6",
  Call: "#22c55e",
  Email: "#a855f7",
  QBR: "#f97316",
};

interface Props {
  data: InteractionTypeBreakdown;
}

export function InteractionTypeChart({ data }: Props) {
  const chartData = [
    { name: "Meeting", value: data.MEETING },
    { name: "Call", value: data.CALL },
    { name: "Email", value: data.EMAIL },
    { name: "QBR", value: data.QBR },
  ].filter((d) => d.value > 0);

  const isEmpty = chartData.length === 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Interaction Type Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <div className="flex items-center justify-center h-[280px] text-sm text-muted-foreground italic">
            No interactions recorded yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={chartData}
              margin={{ top: 4, right: 8, left: -16, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip formatter={(value: number) => [value, "Interactions"]} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={TYPE_COLORS[entry.name] ?? "#6b7280"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
