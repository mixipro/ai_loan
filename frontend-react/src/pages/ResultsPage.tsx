// src/pages/ResultsPage.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowLeft, Trophy, Sparkle, Buildings, House, ChartLine,
  Lightning, MapPin, TrendUp, ChartBar
} from "@phosphor-icons/react";
import { ReturnComparisonBar } from "@/components/charts/ReturnComparisonBar";
import { CashflowLineChart } from "@/components/charts/CashflowLineChart";
import { RiskScatter } from "@/components/charts/RiskScatter";
import { BreakEvenBar } from "@/components/charts/BreakEvenBar";
import { StrategyDetailCard } from "@/components/strategy/StrategyDetailCard";
import type { AnalyzeResponse, Strategy } from "@/types/response";

const formatPct = (v: unknown): string => {
  const n = typeof v === "number" ? v : Number(v);
  if (!isFinite(n)) return "?";
  return `${n > 0 ? "+" : ""}${(n * 100).toFixed(2)}%`;
};

const getAgentIcon = (agent: string) => {
  switch (agent) {
    case "business": return Buildings;
    case "real_estate": return House;
    case "stock": return ChartLine;
    default: return ChartLine;
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

export function ResultsPage() {
  const navigate = useNavigate();
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    const stored = sessionStorage.getItem("analysis_result");
    if (!stored) {
      navigate("/form");
      return;
    }
    try {
      setResult(JSON.parse(stored));
    } catch {
      navigate("/form");
    }
  }, [navigate]);

  if (!result) return null;

  const strategies = result.strategies ?? [];
  const winningStrategy = result.recommendation;
  const winningAgent = winningStrategy?.agent;
  const detailed = result.detailed_explanation;
  const userSummary = result.user_summary;
  const charts = result.comparison_charts;

  return (
    <div className="container mx-auto py-6 max-w-7xl px-4 animate-fade-in">
      {/* ─── HEADER ─── */}
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate("/form")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to form
        </Button>
        <div className="flex items-center gap-2 text-xs">
          {result.profile_used && (
            <Badge variant="secondary" className="capitalize">
              {result.profile_used} risk profile
            </Badge>
          )}
          <Badge variant="outline">v5.2.5</Badge>
        </div>
      </div>

      {/* ─── TITLE ─── */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight mb-2 flex items-center gap-3">
          <Sparkle weight="duotone" className="text-primary h-9 w-9" />
          Your Investment Analysis
        </h1>
        {userSummary && (
          <p className="text-muted-foreground flex items-center gap-2 text-sm">
            <MapPin weight="duotone" className="h-4 w-4" />
            {userSummary.age}-year-old in {userSummary.city}, {userSummary.region.replace("_", " ")}
            <span className="mx-1">·</span>
            Income: ${userSummary.income?.toLocaleString()}/mo
            <span className="mx-1">·</span>
            Savings: ${userSummary.savings?.toLocaleString()}
          </p>
        )}
      </div>

      {/* ─── WINNER BANNER ─── */}
      {winningStrategy && (
        <Card className="mb-8 border-primary border-2 overflow-hidden">
          <div className="bg-gradient-to-br from-primary/10 via-primary/5 to-transparent">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="p-3 rounded-xl bg-yellow-100 shadow-sm">
                    <Trophy weight="fill" className="text-yellow-500 h-8 w-8" />
                  </div>
                  <div>
                    <Badge variant="default" className="mb-2 gap-1">
                      <Sparkle weight="fill" className="h-3 w-3" />
                      Recommended for you
                    </Badge>
                    <CardTitle className="text-2xl leading-tight">
                      {winningStrategy.title}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {getAgentLabel(winningAgent)} · {winningStrategy.type}
                    </CardDescription>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-xs text-muted-foreground">Y3 Net Return</div>
                  <div className={`text-3xl font-bold tabular-nums ${
                    winningStrategy.net_return > 0 ? "text-emerald-600" : "text-red-600"
                  }`}>
                    {formatPct(winningStrategy.net_return)}
                  </div>
                  <div className="text-xs text-muted-foreground tabular-nums">
                    ({winningStrategy.net_return_dollars > 0 ? "+" : ""}${Math.abs(winningStrategy.net_return_dollars).toLocaleString()})
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Headline */}
              {detailed?.headline && (
                <p className="font-medium leading-relaxed text-base">
                  {detailed.headline}
                </p>
              )}

              {/* Why chosen */}
              {detailed?.why_chosen && (
                <div className="bg-background/60 backdrop-blur p-4 rounded-lg border">
                  <h4 className="font-semibold text-sm mb-2 flex items-center gap-1.5">
                    <Lightning weight="fill" className="h-4 w-4 text-primary" />
                    Why this strategy
                  </h4>
                  <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                    {detailed.why_chosen}
                  </p>
                </div>
              )}

              {/* California Angle */}
              {detailed?.california_angle && (
                <div className="bg-orange-50 border border-orange-200 p-4 rounded-lg">
                  <h4 className="font-semibold text-sm mb-2 flex items-center gap-1.5 text-orange-900">
                    🌴 California Angle
                  </h4>
                  <p className="text-sm text-orange-900/80 leading-relaxed whitespace-pre-wrap">
                    {detailed.california_angle}
                  </p>
                </div>
              )}

              {/* Action plan */}
              {Array.isArray(detailed?.action_plan) && detailed.action_plan.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-2 flex items-center gap-1.5">
                    <TrendUp weight="duotone" className="h-4 w-4" />
                    Action plan
                  </h4>
                  <ol className="space-y-1.5">
                    {detailed.action_plan.map((step, i) => (
                      <li key={i} className="text-sm flex gap-2">
                        <span className="font-semibold text-primary shrink-0">{i + 1}.</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </CardContent>
          </div>
        </Card>
      )}

      {/* ─── TABS ─── */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 mb-4">
          <TabsTrigger value="overview" className="gap-1.5">
            <ChartBar weight="duotone" className="h-4 w-4" />
            Overview
          </TabsTrigger>
          {strategies.map((s) => {
            const Icon = getAgentIcon(s.agent);
            return (
              <TabsTrigger key={s.agent} value={s.agent} className="gap-1.5">
                <Icon weight="duotone" className="h-4 w-4" />
                {getAgentLabel(s.agent)}
                {s.agent === winningAgent && <Trophy weight="fill" className="h-3 w-3 text-yellow-500" />}
              </TabsTrigger>
            );
          })}
        </TabsList>

        {/* ─── OVERVIEW TAB ─── */}
        <TabsContent value="overview" className="space-y-6 animate-fade-in">
          {/* Charts grid */}
          {charts && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{charts.return_chart.title}</CardTitle>
                  <CardDescription className="text-xs">{charts.return_chart.subtitle}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ReturnComparisonBar data={charts.return_chart} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{charts.cashflow_chart.title}</CardTitle>
                  <CardDescription className="text-xs">{charts.cashflow_chart.subtitle}</CardDescription>
                </CardHeader>
                <CardContent>
                  <CashflowLineChart data={charts.cashflow_chart} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{charts.risk_chart.title}</CardTitle>
                  <CardDescription className="text-xs">{charts.risk_chart.subtitle}</CardDescription>
                </CardHeader>
                <CardContent>
                  <RiskScatter data={charts.risk_chart} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{charts.timeline_chart.title}</CardTitle>
                  <CardDescription className="text-xs">{charts.timeline_chart.subtitle}</CardDescription>
                </CardHeader>
                <CardContent>
                  <BreakEvenBar data={charts.timeline_chart} />
                </CardContent>
              </Card>
            </div>
          )}

          {/* Summary cards */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">All three strategies — quick comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {strategies.map((s: Strategy) => {
                  const Icon = getAgentIcon(s.agent);
                  const isWinner = s.agent === winningAgent;
                  return (
                    <button
                      key={s.agent}
                      type="button"
                      onClick={() => setActiveTab(s.agent)}
                      className={`
                        text-left p-4 rounded-lg border transition-all hover:shadow-md
                        ${isWinner ? "border-primary border-2 bg-primary/5" : "border-border hover:border-primary"}
                      `}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Icon weight="duotone" className="h-5 w-5" />
                        <span className="font-medium">{getAgentLabel(s.agent)}</span>
                        {isWinner && <Trophy weight="fill" className="h-4 w-4 text-yellow-500 ml-auto" />}
                      </div>
                      <div className="text-xs text-muted-foreground mb-2 line-clamp-2">
                        {s.title}
                      </div>
                      <div className="flex items-baseline justify-between">
                        <Badge variant={
                          s.status === "profitable" ? "default" :
                          s.status === "marginal" ? "secondary" :
                          "destructive"
                        } className="text-xs">
                          {s.status}
                        </Badge>
                        <div className={`text-lg font-bold tabular-nums ${
                          s.net_return > 0 ? "text-emerald-600" : "text-red-600"
                        }`}>
                          {formatPct(s.net_return)}
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-primary font-medium">
                        Click for details →
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Risk analysis from detailed */}
          {detailed?.risk_analysis && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Risk Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {detailed.risk_analysis}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Comparison */}
          {detailed?.comparative_analysis && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Comparative Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {detailed.comparative_analysis}
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ─── PER-STRATEGY TABS ─── */}
        {strategies.map((s) => (
          <TabsContent key={s.agent} value={s.agent}>
            <StrategyDetailCard strategy={s} isWinner={s.agent === winningAgent} />
          </TabsContent>
        ))}
      </Tabs>

      {/* Debug */}
      <details className="mt-12">
        <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
          🐛 Debug: Show raw JSON
        </summary>
        <pre className="mt-2 p-3 bg-muted rounded text-[10px] overflow-auto max-h-96">
          {JSON.stringify(result, null, 2)}
        </pre>
      </details>
    </div>
  );
}
