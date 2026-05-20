// src/components/charts/ScenariosBar.tsx
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine
} from "recharts";

interface ScenarioData {
  case_name: string;
  total_roi_pct: number;
  narrative: string;
  color: string;
}

interface Props {
  bestRoi: number;
  baseRoi: number;
  worstRoi: number;
  bestNarrative?: string;
  baseNarrative?: string;
  worstNarrative?: string;
}

export function ScenariosBar({
  bestRoi, baseRoi, worstRoi,
  bestNarrative, baseNarrative, worstNarrative,
}: Props) {
  const data: ScenarioData[] = [
    { case_name: "Worst", total_roi_pct: worstRoi, narrative: worstNarrative ?? "", color: "#ef4444" },
    { case_name: "Base", total_roi_pct: baseRoi, narrative: baseNarrative ?? "", color: "#f59e0b" },
    { case_name: "Best", total_roi_pct: bestRoi, narrative: bestNarrative ?? "", color: "#10b981" },
  ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 16, right: 16, left: 8, bottom: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
        <XAxis
          dataKey="case_name"
          tick={{ fontSize: 12, fill: "hsl(var(--foreground))" }}
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
            maxWidth: "260px",
          }}
          formatter={(value: number, _name, item) => {
            const d = item.payload as ScenarioData;
            return [
              <div key="tt" className="space-y-1">
                <div className="font-semibold">{value > 0 ? "+" : ""}{value.toFixed(1)}% ROI</div>
                {d.narrative && (
                  <div className="text-xs text-muted-foreground" style={{ whiteSpace: "normal" }}>
                    {d.narrative}
                  </div>
                )}
              </div>,
              "",
            ];
          }}
        />
        <Bar dataKey="total_roi_pct" radius={[6, 6, 0, 0]}>
          {data.map((entry, idx) => (
            <Cell key={idx} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
