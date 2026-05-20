// src/components/charts/AllocationDonut.tsx
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend
} from "recharts";

interface Props {
  allocation: Record<string, number>;
  colorScheme?: "blue" | "green" | "orange";
}

const COLOR_SCHEMES: Record<string, string[]> = {
  blue: ["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe"],
  green: ["#16a34a", "#22c55e", "#4ade80", "#86efac", "#bbf7d0"],
  orange: ["#ea580c", "#f97316", "#fb923c", "#fdba74", "#fed7aa"],
};

const formatLabel = (key: string): string =>
  key.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");

export function AllocationDonut({ allocation, colorScheme = "blue" }: Props) {
  const colors = COLOR_SCHEMES[colorScheme] ?? COLOR_SCHEMES.blue;

  // Filter out zero values
  const data = Object.entries(allocation)
    .filter(([_, val]) => val > 0)
    .map(([key, val]) => ({
      name: formatLabel(key),
      value: val,
    }));

  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[280px] text-muted-foreground text-sm">
        No allocation data
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((_, idx) => (
              <Cell key={idx} fill={colors[idx % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              fontSize: "12px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            }}
            formatter={(value: number, name: string) => {
              const pct = ((value / total) * 100).toFixed(1);
              return [`$${value.toLocaleString()} (${pct}%)`, name];
            }}
          />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Center total label */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none" style={{ paddingBottom: 50 }}>
        <div className="text-center">
          <div className="text-xs text-muted-foreground">Total</div>
          <div className="text-lg font-semibold tabular-nums">${total.toLocaleString()}</div>
        </div>
      </div>
    </div>
  );
}
