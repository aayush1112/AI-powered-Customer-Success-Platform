"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CustomerStatusBreakdown } from "../types";

const SLICES = [
  { key: "ACTIVE" as const, name: "Active", color: "#22c55e" },
  { key: "AT_RISK" as const, name: "At Risk", color: "#eab308" },
  { key: "CHURNED" as const, name: "Churned", color: "#ef4444" },
  { key: "PROSPECT" as const, name: "Prospect", color: "#3b82f6" },
];

interface Props {
  data: CustomerStatusBreakdown;
}

export function CustomerStatusChart({ data }: Props) {
  const chartData = SLICES.map((s) => ({
    name: s.name,
    value: data[s.key],
    color: s.color,
  })).filter((d) => d.value > 0);

  const isEmpty = chartData.length === 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Customer Status Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <div className="flex items-center justify-center h-[280px] text-sm text-muted-foreground italic">
            No customer data yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                labelLine={false}
              >
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => [value, "Customers"]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
