"use client";

import {
  Bar,
  BarChart,
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
import type { RiskItem } from "../types";

const TRUNCATE_LENGTH = 32;

function truncate(text: string): string {
  return text.length > TRUNCATE_LENGTH
    ? `${text.slice(0, TRUNCATE_LENGTH)}…`
    : text;
}

interface Props {
  data: RiskItem[];
}

export function TopRisksChart({ data }: Props) {
  const isEmpty = data.length === 0;

  const chartData = data.map((item) => ({
    name: truncate(item.risk),
    fullName: item.risk,
    value: item.count,
  }));

  const barHeight = 36;
  const chartHeight = Math.max(200, chartData.length * barHeight + 40);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Top Identified Risks</CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground italic">
            No risks extracted yet. Generate AI insights to see risks.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart
              layout="vertical"
              data={chartData}
              margin={{ top: 4, right: 40, left: 8, bottom: 4 }}
            >
              <XAxis
                type="number"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                width={160}
              />
              <Tooltip
                formatter={(value: number) => [value, "Occurrences"]}
                labelFormatter={(_: unknown, payload: unknown[]) => {
                  const p = payload as Array<{ payload: { fullName: string } }>;
                  return p[0]?.payload?.fullName ?? "";
                }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} label={{ position: "right", fontSize: 11 }}>
                {chartData.map((_, index) => (
                  <Cell key={index} fill="#ef4444" fillOpacity={0.75 - index * 0.05} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
