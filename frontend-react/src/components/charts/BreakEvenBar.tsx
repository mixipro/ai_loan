// src/components/charts/BreakEvenBar.tsx
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList
} from "recharts";
import type { TimelineChart } from "@/types/response";

interface Props {
  data: TimelineChart;
}

export function BreakEvenBar({ data }: Props) {
  // Sort ascending — fastest break-even first
  const chartData = [...data.data]
    .sort((a, b) => a.value - b.value)
    .map((d) => ({
      name: d.label,
      value: d.value,
      color: d.color,
      formatted: d.formatted,
    }));

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 16, right: 80, left: 8, bottom: 16 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            axisLine={{ stroke: "hsl(var(--border))" }}
            tickFormatter={(v) => `${v}mo`}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 12, fill: "hsl(var(--foreground))" }}
            axisLine={{ stroke: "hsl(var(--border))" }}
            width={100}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              fontSize: "12px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            }}
            formatter={(_value: number, _name, item) => {
              const d = item.payload as { formatted: string };
              return [d.formatted, "Time to break-even"];
            }}
          />
          <Bar dataKey="value" radius={[0, 6, 6, 0]}>
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} />
            ))}
            <LabelList
              dataKey="formatted"
              position="right"
              style={{ fontSize: 11, fill: "hsl(var(--foreground))" }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
