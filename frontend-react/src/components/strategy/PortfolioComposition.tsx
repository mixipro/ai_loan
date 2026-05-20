// src/components/strategy/PortfolioComposition.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Briefcase } from "@phosphor-icons/react";
import type { PortfolioComposition as PortfolioType } from "@/types/response";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip
} from "recharts";

interface Props {
  composition: PortfolioType;
}

const COLORS = ["#2563eb", "#7c3aed", "#ea580c", "#16a34a", "#dc2626"];

export function PortfolioComposition({ composition }: Props) {
  const data = composition.asset_classes.map((a, idx) => ({
    name: a.ticker,
    fullName: a.name,
    value: a.weight_pct,
    expected: a.expected_return_pct,
    color: COLORS[idx % COLORS.length],
  }));

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Briefcase weight="duotone" className="h-5 w-5 text-purple-500" />
          Portfolio Composition
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Pie */}
          <div>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={48}
                  outerRadius={85}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name }) => name}
                  labelLine={false}
                >
                  {data.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  formatter={(_v, _name, item) => {
                    const d = item.payload as { fullName: string; value: number; expected: number };
                    return [
                      `${d.value}% — Expected: ${d.expected}%`,
                      d.fullName,
                    ];
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* List */}
          <div className="space-y-2">
            {data.map((asset, idx) => (
              <div
                key={asset.name}
                className="flex items-center justify-between p-2 rounded border bg-background"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: asset.color }}
                  />
                  <div>
                    <div className="text-sm font-medium">{asset.name}</div>
                    <div className="text-xs text-muted-foreground">{asset.fullName}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold tabular-nums">{asset.value}%</div>
                  <div className="text-xs text-emerald-600 tabular-nums">+{asset.expected}%</div>
                </div>
              </div>
            ))}

            <div className="mt-4 pt-3 border-t flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Blended Return:</span>
              <Badge variant="default">{composition.blended_expected_return_pct}%</Badge>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Dividend Yield:</span>
              <span className="font-medium tabular-nums">{composition.dividend_yield_pct}%</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Expense Ratio:</span>
              <span className="font-medium tabular-nums">{composition.expense_ratio_pct}%</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
