// src/components/charts/RiskScatter.tsx
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ZAxis, ResponsiveContainer, Cell, ReferenceArea
} from "recharts";
import type { RiskChart } from "@/types/response";

interface Props {
  data: RiskChart;
}

export function RiskScatter({ data }: Props) {
  const chartData = data.data.map((d) => ({
    name: d.label,
    x: d.x,
    y: d.y,
    z: d.size * 20, // Scale bubble size
    color: d.color,
  }));

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 16, right: 20, left: 12, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
          <XAxis
            type="number"
            dataKey="x"
            name="Risk"
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            label={{ value: "Risk Level", position: "insideBottom", offset: -10, fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Stability"
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            label={{ value: "Stability", angle: -90, position: "insideLeft", fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          />
          <ZAxis type="number" dataKey="z" range={[120, 600]} />

          {/* Ideal zone — low risk, high stability */}
          <ReferenceArea x1={0} x2={40} y1={70} y2={100} fill="#10b981" fillOpacity={0.05} />

          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              fontSize: "12px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            }}
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(value: number, name: string) => {
              if (name === "z") return [null, null];
              return [`${value}`, name];
            }}
            labelFormatter={(_label, payload) => {
              return payload?.[0]?.payload?.name ?? "";
            }}
          />
          <Scatter data={chartData} fill="#8884d8">
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} stroke={entry.color} strokeWidth={2} fillOpacity={0.7} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
