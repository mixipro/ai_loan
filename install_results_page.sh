#!/bin/bash
# Quick fix: install latest ResultsPage.tsx
set -e

if [ ! -d "frontend-react" ]; then
    echo "Run from project root: ~/PycharmProjects/ai_loan"
    exit 1
fi

echo "Installing ResultsPage.tsx..."
cat > frontend-react/src/pages/ResultsPage.tsx << 'FILE_EOF'
// src/pages/ResultsPage.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Trophy, Buildings, House, ChartLine, Sparkle } from "@phosphor-icons/react";

// ─────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────
const formatPct = (v: unknown): string => {
  const n = typeof v === "number" ? v : Number(v);
  if (!isFinite(n)) return "?";
  return `${(n * 100).toFixed(2)}%`;
};

const formatUSD = (v: unknown): string => {
  const n = typeof v === "number" ? v : Number(v);
  if (!isFinite(n)) return "?";
  return `$${n.toLocaleString()}`;
};

const getAgentIcon = (agent: string) => {
  switch (agent) {
    case "business": return Buildings;
    case "real_estate": return House;
    case "stock": return ChartLine;
    default: return ChartLine;
  }
};

const getAgentColor = (agent: string) => {
  switch (agent) {
    case "business": return "text-blue-500";
    case "real_estate": return "text-green-500";
    case "stock": return "text-purple-500";
    default: return "text-gray-500";
  }
};

const getAgentLabel = (agent: string) => {
  switch (agent) {
    case "business": return "Business";
    case "real_estate": return "Real Estate";
    case "stock": return "Stocks/ETFs";
    default: return agent;
  }
};

const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
  switch (status) {
    case "profitable": return "default";
    case "marginal": return "secondary";
    case "not_profitable": return "destructive";
    case "rejected": return "outline";
    default: return "outline";
  }
};

// ─────────────────────────────────────────────────────────────
// COMPONENT
// ─────────────────────────────────────────────────────────────
export function ResultsPage() {
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("analysis_result");
    if (!stored) {
      navigate("/form");
      return;
    }
    try {
      setResult(JSON.parse(stored));
    } catch (e) {
      setError(`Failed to parse result: ${e}`);
    }
  }, [navigate]);

  if (error) {
    return (
      <div className="container mx-auto py-8 max-w-3xl">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error loading results</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm mb-4">{error}</p>
            <Button onClick={() => navigate("/form")}>← Back to form</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!result) return null;

  // ─── Defensive extraction (correct backend shape!) ───
  const strategies = Array.isArray(result.strategies) ? result.strategies : [];
  const recommendation = result.recommendation;
  // recommendation is the WINNING STRATEGY (full object copy)
  const winningStrategy = recommendation && typeof recommendation === "object" ? recommendation : null;
  const winningAgent = winningStrategy?.agent ?? "?";

  // Judge narrative is in TOP-LEVEL fields
  const reasoning = typeof result.reasoning === "string" ? result.reasoning : "";
  const comparison = typeof result.comparison === "string" ? result.comparison : "";
  const nextStep = typeof result.next_step === "string" ? result.next_step : "";

  // Structured judge breakdown
  const detailed = result.detailed_explanation && typeof result.detailed_explanation === "object"
    ? result.detailed_explanation : null;

  // User summary (it's an OBJECT, not string!)
  const userSummary = result.user_summary && typeof result.user_summary === "object"
    ? result.user_summary : null;

  return (
    <div className="container mx-auto py-8 max-w-6xl">
      {/* ─── HEADER ─── */}
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" onClick={() => navigate("/form")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to form
        </Button>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {strategies.length} strategies generated
          </Badge>
          {result.profile_used && (
            <Badge variant="secondary" className="capitalize">
              Profile: {result.profile_used} risk
            </Badge>
          )}
        </div>
      </div>

      <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
        <Sparkle weight="duotone" className="text-primary h-8 w-8" />
        Your Investment Analysis
      </h1>

      {/* ─── USER SUMMARY ─── */}
      {userSummary && (
        <p className="text-muted-foreground mb-8 text-sm">
          {userSummary.age}-year-old in {userSummary.city}, {userSummary.region} ·{" "}
          Income: ${userSummary.income?.toLocaleString()}/mo
        </p>
      )}

      {/* ─── WINNER BANNER ─── */}
      {winningStrategy && (
        <Card className="mb-8 border-primary border-2 bg-gradient-to-br from-primary/5 to-transparent">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Trophy weight="fill" className="text-yellow-500 h-8 w-8" />
                <div>
                  <Badge variant="default" className="mb-2">
                    Recommended Strategy
                  </Badge>
                  <CardTitle className="text-2xl">
                    {winningStrategy.title || getAgentLabel(winningAgent)}
                  </CardTitle>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground">Y3 Net Return</div>
                <div className={`text-2xl font-bold ${
                  (winningStrategy.net_return ?? 0) > 0 ? "text-green-600" : "text-red-600"
                }`}>
                  {formatPct(winningStrategy.net_return)}
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Structured detailed_explanation */}
            {detailed?.headline && (
              <p className="font-medium leading-relaxed">{detailed.headline}</p>
            )}
            {detailed?.why_chosen && (
              <div>
                <h4 className="font-semibold text-sm mb-1">Why This Strategy</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {detailed.why_chosen}
                </p>
              </div>
            )}
            {/* Fallback to top-level reasoning if no detailed */}
            {!detailed?.why_chosen && reasoning && (
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{reasoning}</p>
            )}

            {detailed?.comparative_analysis && (
              <div>
                <h4 className="font-semibold text-sm mb-1">How It Compares</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {detailed.comparative_analysis}
                </p>
              </div>
            )}
            {!detailed?.comparative_analysis && comparison && (
              <div>
                <h4 className="font-semibold text-sm mb-1">Comparison</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {comparison}
                </p>
              </div>
            )}

            {detailed?.risk_analysis && (
              <div>
                <h4 className="font-semibold text-sm mb-1">Risk Analysis</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {detailed.risk_analysis}
                </p>
              </div>
            )}

            {detailed?.california_angle && (
              <div className="p-3 bg-orange-50 dark:bg-orange-950/20 rounded">
                <h4 className="font-semibold text-sm mb-1 text-orange-700 dark:text-orange-300">
                  🌴 California Angle
                </h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {detailed.california_angle}
                </p>
              </div>
            )}

            {nextStep && (
              <div className="pt-4 border-t">
                <h4 className="font-semibold text-sm mb-1">Next Step</h4>
                <p className="text-sm text-primary">{nextStep}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ─── ALL 3 STRATEGIES ─── */}
      <h2 className="text-xl font-semibold mb-4">All Three Strategies</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {strategies.map((strategy: any, idx: number) => {
          const Icon = getAgentIcon(strategy.agent);
          const colorClass = getAgentColor(strategy.agent);
          const status = strategy.status || strategy.derived_status_override || "?";
          const netReturn = strategy.net_return ?? 0;
          const isWinner = strategy.agent === winningAgent;

          return (
            <Card
              key={strategy.agent || idx}
              className={isWinner ? "border-primary border-2" : ""}
            >
              <CardHeader>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Icon weight="duotone" className={`h-5 w-5 ${colorClass}`} />
                    <CardTitle className="text-lg">
                      {getAgentLabel(strategy.agent)}
                    </CardTitle>
                  </div>
                  {isWinner && (
                    <Trophy weight="fill" className="h-4 w-4 text-yellow-500" />
                  )}
                </div>
                <CardDescription className="text-xs line-clamp-2">
                  {strategy.title || "Untitled"}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Status:</span>
                  <Badge variant={getStatusVariant(status)}>{status}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Net return:</span>
                  <span className={netReturn > 0 ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
                    {formatPct(netReturn)}
                  </span>
                </div>
                {strategy.type && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Type:</span>
                    <Badge variant="outline" className="text-xs">
                      {strategy.type}
                    </Badge>
                  </div>
                )}
                {strategy.total_capital !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Capital:</span>
                    <span>{formatUSD(strategy.total_capital)}</span>
                  </div>
                )}
                {strategy.funding_mode && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Funding:</span>
                    <span className="capitalize">{strategy.funding_mode}</span>
                  </div>
                )}

                <Separator className="my-2" />

                {/* Pros (first 2) */}
                {Array.isArray(strategy.pros) && strategy.pros.length > 0 && (
                  <div>
                    <h5 className="text-xs font-semibold mb-1 text-green-700 dark:text-green-400">
                      Pros
                    </h5>
                    <ul className="text-xs space-y-1 text-muted-foreground">
                      {strategy.pros.slice(0, 2).map((pro: string, i: number) => (
                        <li key={i} className="flex gap-1">
                          <span className="text-green-600">✓</span>
                          <span className="line-clamp-2">{pro}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Cons (first 2) */}
                {Array.isArray(strategy.cons) && strategy.cons.length > 0 && (
                  <div>
                    <h5 className="text-xs font-semibold mb-1 text-red-700 dark:text-red-400">
                      Cons
                    </h5>
                    <ul className="text-xs space-y-1 text-muted-foreground">
                      {strategy.cons.slice(0, 2).map((con: string, i: number) => (
                        <li key={i} className="flex gap-1">
                          <span className="text-red-600">✗</span>
                          <span className="line-clamp-2">{con}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Rejection */}
                {strategy.rejected && strategy.rejection_reason && (
                  <div className="mt-2 bg-red-50 dark:bg-red-950/20 p-2 rounded">
                    <p className="text-xs text-red-600 dark:text-red-400">
                      <strong>Rejected:</strong> {strategy.rejection_reason}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* ─── DAY 2 PLACEHOLDER ─── */}
      <Card className="mt-8 border-dashed">
        <CardHeader>
          <CardTitle className="text-muted-foreground text-sm">
            🚧 Day 2 (charts & detailed breakdown)
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-1">
          <p>• Recharts: allocation pies, projections lines, scenarios bars</p>
          <p>• Step-by-step calculation breakdown UI</p>
          <p>• Next steps action items</p>
          <p>• Detailed per-strategy view</p>
        </CardContent>
      </Card>

      {/* ─── DEBUG ─── */}
      <details className="mt-8">
        <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
          🐛 Debug: Show raw JSON response
        </summary>
        <pre className="mt-2 p-4 bg-muted rounded text-xs overflow-auto max-h-96">
          {JSON.stringify(result, null, 2)}
        </pre>
      </details>
    </div>
  );
}
FILE_EOF
echo "✓ Done"
