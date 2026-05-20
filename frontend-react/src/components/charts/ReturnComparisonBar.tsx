// src/components/charts/ReturnComparisonBar.tsx
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer, ReferenceLine
} from "recharts";
import type { ReturnChart } from "@/types/response";

interface Props {
  data: ReturnChart;
}

export function ReturnComparisonBar({ data }: Props) {
  const chartData = data.data.map((d) => ({
    name: d.label,
    value: d.value,
    color: d.color,
    absolute: d.absolute_usd,
    formatted: d.formatted,
  }));

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} margin={{ top: 20, right: 16, left: 8, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
            axisLine={{ stroke: "hsl(var(--border))" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            axisLine={{ stroke: "hsl(var(--border))" }}
            tickFormatter={(v) => `${v}%`}
          />
          <ReferenceLine y={0} stroke="hsl(var(--foreground))" strokeWidth={1} />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              fontSize: "12px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            }}
            formatter={(value: number, _name, item) => {
              const d = item.payload as { absolute: number };
              return [
                `${value > 0 ? "+" : ""}${value.toFixed(2)}% (${d.absolute > 0 ? "+" : ""}$${Math.abs(d.absolute).toLocaleString()})`,
                "Net Return",
              ];
            }}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
