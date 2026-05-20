// src/components/strategy/StrategyDetailCard.tsx
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Buildings, House, ChartLine, Trophy, CheckCircle, XCircle, Lightning, Bank, Lightning as Spark } from "@phosphor-icons/react";
import { AllocationDonut } from "@/components/charts/AllocationDonut";
import { ScenariosBar } from "@/components/charts/ScenariosBar";
import { CalculationBreakdown } from "./CalculationBreakdown";
import { PortfolioComposition } from "./PortfolioComposition";
import type { Strategy } from "@/types/response";

interface Props {
  strategy: Strategy;
  isWinner?: boolean;
}

const formatPct = (v: unknown): string => {
  const n = typeof v === "number" ? v : Number(v);
  if (!isFinite(n)) return "?";
  return `${n > 0 ? "+" : ""}${(n * 100).toFixed(2)}%`;
};

const formatUSD = (v: unknown): string => {
  const n = typeof v === "number" ? v : Number(v);
  if (!isFinite(n)) return "?";
  return `$${Math.round(n).toLocaleString()}`;
};

const getAgentMeta = (agent: string) => {
  switch (agent) {
    case "business":
      return { Icon: Buildings, color: "text-blue-500", bg: "bg-blue-50", scheme: "blue" as const, label: "Business" };
    case "real_estate":
      return { Icon: House, color: "text-emerald-500", bg: "bg-emerald-50", scheme: "green" as const, label: "Real Estate" };
    case "stock":
      return { Icon: ChartLine, color: "text-orange-500", bg: "bg-orange-50", scheme: "orange" as const, label: "Stocks/ETFs" };
    default:
      return { Icon: ChartLine, color: "text-gray-500", bg: "bg-gray-50", scheme: "blue" as const, label: agent };
  }
};

const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
  switch (status) {
    case "profitable": return "default";
    case "marginal": return "secondary";
    case "not_profitable": return "destructive";
    default: return "outline";
  }
};

export function StrategyDetailCard({ strategy, isWinner }: Props) {
  const meta = getAgentMeta(strategy.agent);
  const { Icon, color, bg, scheme, label } = meta;

  // Get scenarios in normalized format
  const scenarios = strategy.scenarios;
  let bestRoi = 0, baseRoi = 0, worstRoi = 0;
  let bestNarr = "", baseNarr = "", worstNarr = "";

  if (scenarios) {
    // Different agents have different keys — normalize
    if (strategy.agent === "business") {
      bestRoi = scenarios.best_case.annual_return_pct ?? 0;
      baseRoi = scenarios.base_case.annual_return_pct ?? 0;
      worstRoi = scenarios.worst_case.annual_return_pct ?? 0;
    } else {
      // RE + stock both have total_roi_pct
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      bestRoi = (scenarios.best_case as any).total_roi_pct ?? 0;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      baseRoi = (scenarios.base_case as any).total_roi_pct ?? 0;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      worstRoi = (scenarios.worst_case as any).total_roi_pct ?? 0;
    }
    bestNarr = scenarios.best_case.narrative ?? "";
    baseNarr = scenarios.base_case.narrative ?? "";
    worstNarr = scenarios.worst_case.narrative ?? "";
  }

  // Rejection case
  if (strategy.rejected) {
    return (
      <Card className="border-destructive/30 bg-destructive/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Icon weight="duotone" className={`h-5 w-5 ${color}`} />
            {label} — Strategy Rejected
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3">{strategy.rejection_reason}</p>
          {strategy.next_steps && strategy.next_steps.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-semibold mb-1">Next steps:</p>
              {strategy.next_steps.map((step, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <span className="text-primary mt-0.5">→</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Hero Card */}
      <Card className={isWinner ? "border-primary border-2 shadow-md" : ""}>
        <CardHeader className={`${bg} border-b`}>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className={`p-2.5 rounded-lg bg-background shadow-sm`}>
                <Icon weight="duotone" className={`h-6 w-6 ${color}`} />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className="text-xs">{label}</Badge>
                  {isWinner && (
                    <Badge variant="default" className="text-xs gap-1">
                      <Trophy weight="fill" className="h-3 w-3" />
                      Winner
                    </Badge>
                  )}
                </div>
                <CardTitle className="text-lg leading-tight">{strategy.title}</CardTitle>
                <CardDescription className="mt-1 text-xs">
                  Type: <span className="font-medium">{strategy.type}</span> · Funding:{" "}
                  <span className="font-medium capitalize">{strategy.funding_mode}</span>
                </CardDescription>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted-foreground">Net Return</div>
              <div className={`text-2xl font-bold tabular-nums ${
                strategy.net_return > 0 ? "text-emerald-600" : "text-red-600"
              }`}>
                {formatPct(strategy.net_return)}
              </div>
              <Badge variant={getStatusVariant(strategy.status)} className="mt-1 text-xs">
                {strategy.status}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          <p className="text-sm leading-relaxed">{strategy.description}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="p-3 rounded-lg bg-muted">
              <div className="text-xs text-muted-foreground">Total Capital</div>
              <div className="font-semibold tabular-nums">{formatUSD(strategy.total_capital)}</div>
            </div>
            <div className="p-3 rounded-lg bg-muted">
              <div className="text-xs text-muted-foreground">Net Dollars</div>
              <div className={`font-semibold tabular-nums ${
                strategy.net_return_dollars > 0 ? "text-emerald-600" : "text-red-600"
              }`}>
                {strategy.net_return_dollars > 0 ? "+" : ""}{formatUSD(strategy.net_return_dollars)}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted">
              <div className="text-xs text-muted-foreground">Risk</div>
              <div className="font-semibold tabular-nums">{(strategy.risk * 100).toFixed(0)}%</div>
            </div>
            <div className="p-3 rounded-lg bg-muted">
              <div className="text-xs text-muted-foreground">Stability</div>
              <div className="font-semibold tabular-nums">{(strategy.stability * 100).toFixed(0)}%</div>
            </div>
          </div>

          {/* Loan info if applicable */}
          {strategy.uses_loan && strategy.loan_info && strategy.loan_info.amount > 0 && (
            <div className="flex items-start gap-3 p-3 rounded-lg border bg-blue-50/50">
              <Bank weight="duotone" className="h-5 w-5 text-blue-500 mt-0.5 shrink-0" />
              <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <div className="text-muted-foreground">Loan Type</div>
                  <div className="font-medium capitalize">{strategy.loan_info.type}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Amount</div>
                  <div className="font-medium tabular-nums">{formatUSD(strategy.loan_info.amount)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Rate</div>
                  <div className="font-medium tabular-nums">{(strategy.loan_info.rate * 100).toFixed(2)}%</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Monthly</div>
                  <div className="font-medium tabular-nums">{formatUSD(strategy.loan_info.monthly_payment)}</div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Allocation Donut */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Capital Allocation</CardTitle>
          </CardHeader>
          <CardContent>
            <AllocationDonut
              allocation={strategy.allocation as Record<string, number>}
              colorScheme={scheme}
            />
          </CardContent>
        </Card>

        {/* Scenarios Bar */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Best / Base / Worst Case</CardTitle>
            <CardDescription className="text-xs">Annual ROI under different market conditions</CardDescription>
          </CardHeader>
          <CardContent>
            <ScenariosBar
              bestRoi={bestRoi}
              baseRoi={baseRoi}
              worstRoi={worstRoi}
              bestNarrative={bestNarr}
              baseNarrative={baseNarr}
              worstNarrative={worstNarr}
            />
          </CardContent>
        </Card>
      </div>

      {/* Portfolio (Stock only) */}
      {strategy.agent === "stock" && strategy.portfolio_composition && (
        <PortfolioComposition composition={strategy.portfolio_composition} />
      )}

      {/* Property Comparables (RE only) */}
      {strategy.agent === "real_estate" && strategy.property_market_context && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <House weight="duotone" className="h-5 w-5 text-emerald-500" />
              Local Market Context
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Median Property</div>
                <div className="font-semibold tabular-nums">${strategy.property_market_context.median_property_value_usd?.toLocaleString()}</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Median Rent</div>
                <div className="font-semibold tabular-nums">${strategy.property_market_context.median_rent_monthly_usd?.toLocaleString()}/mo</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Rent/Price Ratio</div>
                <div className="font-semibold tabular-nums">{strategy.property_market_context.rent_to_price_ratio_pct}%</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">5yr Appreciation</div>
                <div className="font-semibold tabular-nums">{strategy.property_market_context.appreciation_rate_pct_5yr}%</div>
              </div>
            </div>

            {strategy.property_market_context.comparable_properties?.length > 0 && (
              <div>
                <p className="text-xs font-semibold mb-2">Comparable Properties:</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {strategy.property_market_context.comparable_properties.map((p, i) => (
                    <div key={i} className="text-xs p-2 rounded border bg-background">
                      {p}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <p className="text-xs text-muted-foreground italic">
              {strategy.property_market_context.demand_indicator}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Unit Economics (Business only) */}
      {strategy.agent === "business" && strategy.unit_economics && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Spark weight="duotone" className="h-5 w-5 text-blue-500" />
              Unit Economics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Price per Unit</div>
                <div className="font-semibold tabular-nums">${strategy.unit_economics.price_per_unit_usd}</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Unit Name</div>
                <div className="font-semibold text-xs">{strategy.unit_economics.unit_name}</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Y1 Target</div>
                <div className="font-semibold tabular-nums">{strategy.unit_economics.target_units_year_1?.toLocaleString()}</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Y3 Target</div>
                <div className="font-semibold tabular-nums">{strategy.unit_economics.target_units_year_3?.toLocaleString()}</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Gross Margin</div>
                <div className="font-semibold tabular-nums">{strategy.unit_economics.gross_margin_pct}%</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Revenue Model</div>
                <div className="font-semibold text-xs">{strategy.unit_economics.revenue_model}</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">CAC</div>
                <div className="font-semibold tabular-nums">${strategy.unit_economics.customer_acquisition_cost_usd}</div>
              </div>
              <div className="p-2.5 rounded bg-muted">
                <div className="text-xs text-muted-foreground">Recurring?</div>
                <div className="font-semibold">{strategy.unit_economics.is_recurring ? "Yes" : "No"}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Calculation Breakdown */}
      <CalculationBreakdown breakdown={strategy.calculation_breakdown} />

      {/* Pros / Cons / Next Steps */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2 text-emerald-700">
              <CheckCircle weight="duotone" className="h-4 w-4" />
              Pros
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1.5">
              {strategy.pros.map((pro, i) => (
                <li key={i} className="text-xs flex gap-1.5">
                  <span className="text-emerald-500 shrink-0">✓</span>
                  <span>{pro}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2 text-red-700">
              <XCircle weight="duotone" className="h-4 w-4" />
              Cons
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1.5">
              {strategy.cons.map((con, i) => (
                <li key={i} className="text-xs flex gap-1.5">
                  <span className="text-red-500 shrink-0">✗</span>
                  <span>{con}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2 text-primary">
              <Lightning weight="duotone" className="h-4 w-4" />
              Next Steps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-1.5">
              {strategy.next_steps.map((step, i) => (
                <li key={i} className="text-xs flex gap-1.5">
                  <span className="text-primary font-semibold shrink-0">{i + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
            {strategy.time_to_profit && (
              <>
                <Separator className="my-3" />
                <div className="text-xs">
                  <span className="text-muted-foreground">Time to profit: </span>
                  <span className="font-medium">{strategy.time_to_profit}</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
