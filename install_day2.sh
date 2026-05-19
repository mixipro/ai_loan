#!/bin/bash
# CaliforniaCFO Day 2 — Complete overhaul
set -e

if [ ! -d "frontend-react" ]; then
    echo "Run from project root: ~/PycharmProjects/ai_loan"
    exit 1
fi

echo "Creating folders..."
mkdir -p frontend-react/src/types
mkdir -p frontend-react/src/hooks
mkdir -p frontend-react/src/lib
mkdir -p frontend-react/src/pages
mkdir -p frontend-react/src/components/form
mkdir -p frontend-react/src/components/charts
mkdir -p frontend-react/src/components/strategy
echo "✓ Folders ready"

echo "[1/21] Writing src/types/options.ts..."
cat > frontend-react/src/types/options.ts << 'FILE_EOF_01'
// src/types/options.ts
// Matches backend GET /options response

export interface RegionOption {
  value: string;
  label: string;
  description: string;
  primary_industries: string[];
}

export interface OptionsResponse {
  regions: RegionOption[];
  cities_by_region: Record<string, string[]>;
  currencies: string[];
  sectors: string[];
  professions_by_sector: Record<string, string[]>;
  all_professions: string[];
  employment_statuses: string[];
  tech_roles: string[];
  equity_compensations: string[];
  company_stages: string[];
  entertainment_roles: string[];
  risk_profiles: string[];
  horizons: string[];
  weekly_hours: string[];
  predefined_interests: string[];
}

// Legacy alias for backwards compat (sectors used to be objects)
export interface SectorOption {
  value: string;
  label: string;
}
FILE_EOF_01

echo "[2/21] Writing src/types/response.ts..."
cat > frontend-react/src/types/response.ts << 'FILE_EOF_02'
// src/types/response.ts
// Complete /analyze response shape (matches v5.2.5 backend)

export type AgentName = "business" | "real_estate" | "stock";
export type FundingMode = "cash" | "loan" | "mixed" | "mortgage" | "margin" | "rejected";
export type Status = "profitable" | "marginal" | "not_profitable" | "rejected" | "?";

// ──────── USER SUMMARY ────────
export interface UserSummary {
  region: string;
  city: string;
  country: string;
  age: number;
  income: number;
  expenses: number;
  monthly_debt: number;
  savings: number;
  currency: string;
  risk_profile: string;
  horizon: string;
}

// ──────── RISK ────────
export interface RiskInfo {
  creditworthiness: string;
  explanation: string;
  score: number;
  level: string;
  region: string;
  region_display_name: string;
  region_factor: number;
  cost_of_living_index: number;
  real_disposable_income: number;
  real_savings: number;
  debt_ratio: number;
  base_score: number;
  country: string;
}

// ──────── LOAN INFO ────────
export interface LoanRecord {
  approved: boolean;
  max_loan_amount: number;
  loan_amount: number;
  interest_rate: number;
  loan_years: number;
  monthly_payment: number;
  annual_payment: number;
  total_paid: number;
  total_interest: number;
  loan_type: string;
  savings_to_use: number;
}

export interface LoansBlock {
  business: LoanRecord;
  real_estate: LoanRecord;
  stock_margin: LoanRecord;
  stock: LoanRecord;
}

// ──────── ALLOCATIONS ────────
export interface BusinessAllocation {
  initial_investment: number;
  working_capital: number;
  marketing_budget: number;
  legal_and_setup: number;
  reserve: number;
}

export interface RealEstateAllocation {
  down_payment: number;
  property_value: number;
  taxes_and_fees: number;
  renovation_reserve: number;
  emergency_fund: number;
}

export interface StockAllocation {
  stocks_etfs: number;
  bonds: number;
  reits: number;
  cash_reserve: number;
  international: number;
}

// ──────── PROJECTIONS (per agent) ────────
export interface BusinessProjection {
  revenue: number;
  operating_costs: number;
  loan_payment: number;
  net_cash_flow: number;
}

export interface RealEstateProjection {
  rental_income: number;
  operating_costs: number;
  mortgage_payment: number;
  principal_paid: number;
  appreciation: number;
  cash_flow: number;
  total_return: number;
}

export interface StockProjection {
  dividend_income: number;
  price_appreciation: number;
  margin_interest_cost: number;
  ca_capital_gains_tax: number;
  net_return: number;
}

export interface Projections<T> {
  year_1: T;
  year_3: T;
  year_5: T;
}

// ──────── SCENARIOS (per agent) ────────
export interface BusinessScenario {
  annual_return_pct: number;
  narrative: string;
}

export interface RealEstateScenario {
  appreciation_pct: number;
  cash_flow_pct: number;
  total_roi_pct: number;
  narrative: string;
}

export interface StockScenario {
  price_appreciation_pct: number;
  dividend_yield_pct: number;
  total_roi_pct: number;
  narrative: string;
}

export interface Scenarios<T> {
  best_case: T;
  base_case: T;
  worst_case: T;
}

// ──────── BREAK EVEN ────────
export interface BusinessBreakEven {
  months_to_breakeven: number;
  monthly_revenue_needed_usd: number;
  units_per_month_needed: number;
}

export interface RealEstateBreakEven {
  years_to_breakeven: number;
  cumulative_cash_flow_breakeven_year: number;
  explanation: string;
}

export interface StockBreakEven {
  months_to_breakeven: number;
  drawdown_recovery_months: number;
  explanation: string;
}

// ──────── UNIT ECONOMICS (Business) ────────
export interface UnitEconomics {
  revenue_model: string;
  price_per_unit_usd: number;
  unit_name: string;
  is_recurring: boolean;
  target_units_year_1: number;
  target_units_year_3: number;
  gross_margin_pct: number;
  customer_acquisition_cost_usd: number;
}

// ──────── PORTFOLIO (Stock) ────────
export interface AssetClass {
  name: string;
  ticker: string;
  weight_pct: number;
  expected_return_pct: number;
}

export interface PortfolioComposition {
  asset_classes: AssetClass[];
  blended_expected_return_pct: number;
  dividend_yield_pct: number;
  expense_ratio_pct: number;
}

// ──────── PROPERTY (RE) ────────
export interface PropertyMarketContext {
  median_property_value_usd: number;
  median_rent_monthly_usd: number;
  rent_to_price_ratio_pct: number;
  appreciation_rate_pct_5yr: number;
  comparable_properties: string[];
  demand_indicator: string;
}

export interface PropertyEconomics {
  purchase_price_usd: number;
  down_payment_usd: number;
  monthly_rent_usd: number;
  annual_rental_income_usd: number;
  vacancy_rate_pct: number;
  expected_annual_appreciation_pct: number;
  is_rental: boolean;
  is_flip: boolean;
}

// ──────── MARKET CONTEXT ────────
export interface BusinessMarketContext {
  industry_growth_rate_pct: number;
  key_competitors: string[];
  market_size_local_usd: number;
  demand_indicator: string;
}

export interface StockMarketContext {
  market_regime: string;
  sp500_yoy_change_pct: number;
  vix_level: number;
  ca_capital_gains_tax_pct: number;
  expected_volatility_pct: number;
}

// ──────── MARGIN RISK (Stock) ────────
export interface MarginCallRisk {
  margin_call_probability: number;
  trigger_drawdown_pct: number;
  expected_severity_loss: number;
  explanation: string;
  risk_adjusted_penalty: number;
}

// ──────── CALCULATION BREAKDOWN ────────
export interface CalcStep {
  step: number;
  title: string;
  explanation: string;
  formula: string;
  result: string;
  value_usd?: number;
  value_pct?: number;
  note?: string | null;
}

export interface CalcBreakdown {
  steps: CalcStep[];
  summary: Record<string, number>;
  conclusion: string;
}

// ──────── LOAN INFO (inside strategy) ────────
export interface StrategyLoanInfo {
  type: string;
  amount: number;
  rate: number;
  years: number;
  annual_payment: number;
  monthly_payment: number;
  total_interest: number;
}

// ──────── BASE STRATEGY ────────
interface BaseStrategy {
  agent: AgentName;
  title: string;
  type: string;
  description: string;
  expected_return: number;
  risk: number;
  stability: number;
  pros: string[];
  cons: string[];
  next_steps: string[];
  time_to_profit: string;

  // Funding
  funding_mode: FundingMode;
  loan_amount: number;
  loan_years: number;
  savings_used: number;
  interest_rate: number;
  total_capital: number;
  annual_payment: number;
  loan_info: StrategyLoanInfo;
  uses_loan: boolean;

  // Computed
  nominal_return: number;
  real_return: number;
  net_return: number;
  net_return_dollars: number;
  gross_return_dollars: number;
  status: Status;
  derived_status_override?: string;
  personalized_score: number;
  score: number;
  winning_tier?: string;

  // Common
  rag_sources: string[];
  calculation_breakdown: CalcBreakdown;
  rejected: boolean;
  rejection_reason?: string;
}

// ──────── PER-AGENT STRATEGIES ────────
export interface BusinessStrategy extends BaseStrategy {
  agent: "business";
  allocation: BusinessAllocation;
  market_context: BusinessMarketContext;
  unit_economics: UnitEconomics;
  projections: Projections<BusinessProjection>;
  scenarios: Scenarios<BusinessScenario>;
  break_even: BusinessBreakEven;
}

export interface RealEstateStrategy extends BaseStrategy {
  agent: "real_estate";
  allocation: RealEstateAllocation;
  property_market_context: PropertyMarketContext;
  property_economics: PropertyEconomics;
  projections: Projections<RealEstateProjection>;
  scenarios: Scenarios<RealEstateScenario>;
  break_even: RealEstateBreakEven;
  down_payment_pct: number;
}

export interface StockStrategy extends BaseStrategy {
  agent: "stock";
  allocation: StockAllocation;
  market_context: StockMarketContext;
  portfolio_composition: PortfolioComposition;
  projections: Projections<StockProjection>;
  scenarios: Scenarios<StockScenario>;
  break_even: StockBreakEven;
  margin_call_risk: MarginCallRisk;
}

export type Strategy = BusinessStrategy | RealEstateStrategy | StockStrategy;

// ──────── DETAILED EXPLANATION (Judge) ────────
export interface DetailedExplanation {
  headline: string;
  why_chosen: string;
  comparative_analysis: string;
  risk_analysis: string;
  california_angle: string;
  action_plan: string[];
}

// ──────── COMPARISON CHARTS ────────
export interface ChartDataPoint {
  label: string;
  value: number;
  color: string;
  formatted?: string;
  absolute_usd?: number;
}

export interface ScatterPoint {
  label: string;
  x: number;
  y: number;
  color: string;
  size: number;
}

export interface LineSeries {
  name: string;
  color: string;
  data: number[];
  formatted: string[];
}

export interface ReturnChart {
  type: "bar";
  title: string;
  subtitle: string;
  y_axis_label: string;
  data: ChartDataPoint[];
}

export interface CashflowChart {
  type: "line";
  title: string;
  subtitle: string;
  x_axis_label: string;
  y_axis_label: string;
  categories: string[];
  series: LineSeries[];
}

export interface RiskChart {
  type: "scatter";
  title: string;
  subtitle: string;
  x_axis_label: string;
  y_axis_label: string;
  data: ScatterPoint[];
}

export interface TimelineChart {
  type: "horizontal_bar";
  title: string;
  subtitle: string;
  x_axis_label: string;
  data: ChartDataPoint[];
}

export interface ComparisonCharts {
  return_chart: ReturnChart;
  cashflow_chart: CashflowChart;
  risk_chart: RiskChart;
  timeline_chart: TimelineChart;
}

// ──────── FULL RESPONSE ────────
export interface AnalyzeResponse {
  user_summary: UserSummary;
  risk: RiskInfo;
  config: Record<string, unknown>;
  loans: LoansBlock;
  strategies: Strategy[];
  recommendation: Strategy;  // winning strategy (full copy)
  reasoning: string;
  next_step: string;
  comparison: string;
  profile_used: string;
  rejected_count: number;
  detailed_explanation: DetailedExplanation;
  comparison_charts: ComparisonCharts;
}
FILE_EOF_02

echo "[3/21] Writing src/index.css..."
cat > frontend-react/src/index.css << 'FILE_EOF_03'
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";
@import "@fontsource-variable/geist";
@import "@fontsource-variable/geist-mono";

@custom-variant dark (&:is(.dark *));

@theme inline {
    /* GEIST FONT OVERRIDE — replaces JetBrains Mono everywhere by default */
    --font-sans: 'Geist Variable', system-ui, -apple-system, sans-serif;
    --font-heading: 'Geist Variable', system-ui, sans-serif;
    --font-mono: 'Geist Mono Variable', 'JetBrains Mono', monospace;

    /* Charts/UI sidebar colors */
    --color-sidebar-ring: var(--sidebar-ring);
    --color-sidebar-border: var(--sidebar-border);
    --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
    --color-sidebar-accent: var(--sidebar-accent);
    --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
    --color-sidebar-primary: var(--sidebar-primary);
    --color-sidebar-foreground: var(--sidebar-foreground);
    --color-sidebar: var(--sidebar);
    --color-chart-5: var(--chart-5);
    --color-chart-4: var(--chart-4);
    --color-chart-3: var(--chart-3);
    --color-chart-2: var(--chart-2);
    --color-chart-1: var(--chart-1);
    --color-ring: var(--ring);
    --color-input: var(--input);
    --color-border: var(--border);
    --color-destructive: var(--destructive);
    --color-accent-foreground: var(--accent-foreground);
    --color-accent: var(--accent);
    --color-muted-foreground: var(--muted-foreground);
    --color-muted: var(--muted);
    --color-secondary-foreground: var(--secondary-foreground);
    --color-secondary: var(--secondary);
    --color-primary-foreground: var(--primary-foreground);
    --color-primary: var(--primary);
    --color-popover-foreground: var(--popover-foreground);
    --color-popover: var(--popover);
    --color-card-foreground: var(--card-foreground);
    --color-card: var(--card);
    --color-foreground: var(--foreground);
    --color-background: var(--background);
    --radius-sm: calc(var(--radius) - 4px);
    --radius-md: calc(var(--radius) - 2px);
    --radius-lg: var(--radius);
    --radius-xl: calc(var(--radius) + 4px);
}

:root {
    /* Refined light theme */
    --background: oklch(1 0 0);
    --foreground: oklch(0.145 0 0);
    --card: oklch(1 0 0);
    --card-foreground: oklch(0.145 0 0);
    --popover: oklch(1 0 0);
    --popover-foreground: oklch(0.145 0 0);
    --primary: oklch(0.205 0 0);
    --primary-foreground: oklch(0.985 0 0);
    --secondary: oklch(0.97 0 0);
    --secondary-foreground: oklch(0.205 0 0);
    --muted: oklch(0.97 0 0);
    --muted-foreground: oklch(0.556 0 0);
    --accent: oklch(0.97 0 0);
    --accent-foreground: oklch(0.205 0 0);
    --destructive: oklch(0.577 0.245 27.325);
    --destructive-foreground: oklch(0.985 0 0);
    --border: oklch(0.922 0 0);
    --input: oklch(0.922 0 0);
    --ring: oklch(0.708 0 0);
    --radius: 0.625rem;

    /* Chart colors — for Recharts */
    --chart-1: oklch(0.646 0.222 41.116);
    --chart-2: oklch(0.6 0.118 184.704);
    --chart-3: oklch(0.398 0.07 227.392);
    --chart-4: oklch(0.828 0.189 84.429);
    --chart-5: oklch(0.769 0.188 70.08);

    /* Sidebar */
    --sidebar: oklch(0.985 0 0);
    --sidebar-foreground: oklch(0.145 0 0);
    --sidebar-primary: oklch(0.205 0 0);
    --sidebar-primary-foreground: oklch(0.985 0 0);
    --sidebar-accent: oklch(0.97 0 0);
    --sidebar-accent-foreground: oklch(0.205 0 0);
    --sidebar-border: oklch(0.922 0 0);
    --sidebar-ring: oklch(0.708 0 0);
}

@layer base {
    * {
        @apply border-border;
    }
    html {
        font-family: var(--font-sans);
        font-feature-settings: "cv11", "ss01";
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    body {
        @apply bg-background text-foreground;
        font-family: var(--font-sans);
    }
    code, kbd, pre {
        font-family: var(--font-mono);
    }

    /* Tighter heading typography */
    h1, h2, h3, h4 {
        font-family: var(--font-heading);
        letter-spacing: -0.02em;
        font-weight: 600;
    }

    /* Numbers use Geist Mono for alignment */
    .font-mono, .tabular-nums {
        font-family: var(--font-mono);
        font-feature-settings: "tnum";
    }
}

/* Smooth scrolling */
html {
    scroll-behavior: smooth;
}

/* Animations */
@keyframes fade-in {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
    animation: fade-in 0.4s ease-out;
}

@keyframes slide-up {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-slide-up {
    animation: slide-up 0.5s ease-out;
}
FILE_EOF_03

echo "[4/21] Writing src/main.tsx..."
cat > frontend-react/src/main.tsx << 'FILE_EOF_04'
// src/main.tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App.tsx";

// Fonts — Geist (Vercel) replaces JetBrains Mono for body
import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";

import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>
);
FILE_EOF_04

echo "[5/21] Writing src/components/form/PersonalSection.tsx..."
cat > frontend-react/src/components/form/PersonalSection.tsx << 'FILE_EOF_05'
// src/components/form/PersonalSection.tsx
import { useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AnalyzeRequest } from "@/types/request";

export function PersonalSection() {
  const { register, formState: { errors } } = useFormContext<AnalyzeRequest>();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label htmlFor="age" className="text-sm font-medium">
          Age
        </Label>
        <Input
          id="age"
          type="number"
          min={18}
          max={100}
          {...register("user.personal.age", { valueAsNumber: true, required: true })}
        />
        {errors.user?.personal?.age && (
          <p className="text-xs text-destructive">Age is required (18-100)</p>
        )}
      </div>
    </div>
  );
}
FILE_EOF_05

echo "[6/21] Writing src/components/form/LocationSection.tsx..."
cat > frontend-react/src/components/form/LocationSection.tsx << 'FILE_EOF_06'
// src/components/form/LocationSection.tsx
import { useFormContext, useWatch, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import type { AnalyzeRequest } from "@/types/request";
import type { RegionOption } from "@/types/options";

interface Props {
  regions?: RegionOption[];
  citiesByRegion?: Record<string, string[]>;
}

const FALLBACK_REGIONS: RegionOption[] = [
  { value: "BAY_AREA", label: "Bay Area", description: "", primary_industries: [] },
  { value: "LOS_ANGELES", label: "Los Angeles", description: "", primary_industries: [] },
  { value: "SAN_DIEGO", label: "San Diego", description: "", primary_industries: [] },
];

export function LocationSection({ regions, citiesByRegion }: Props) {
  const { control, setValue } = useFormContext<AnalyzeRequest>();
  const selectedRegion = useWatch({ control, name: "user.location.region" });

  const safeRegions = (regions && regions.length > 0) ? regions : FALLBACK_REGIONS;
  const safeCitiesByRegion = citiesByRegion ?? {};
  const cities = safeCitiesByRegion[selectedRegion] ?? [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label className="text-sm font-medium">Region</Label>
        <Controller
          control={control}
          name="user.location.region"
          render={({ field }) => (
            <Select
              value={field.value}
              onValueChange={(v) => {
                field.onChange(v);
                const firstCity = safeCitiesByRegion[v]?.[0] ?? "";
                setValue("user.location.city", firstCity);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a region" />
              </SelectTrigger>
              <SelectContent>
                {safeRegions.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="space-y-2">
        <Label className="text-sm font-medium">City</Label>
        <Controller
          control={control}
          name="user.location.city"
          render={({ field }) => (
            cities.length > 0 ? (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a city" />
                </SelectTrigger>
                <SelectContent className="max-h-72">
                  {cities.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input placeholder="Enter city name" {...field} />
            )
          )}
        />
      </div>
    </div>
  );
}
FILE_EOF_06

echo "[7/21] Writing src/components/form/FinancialSection.tsx..."
cat > frontend-react/src/components/form/FinancialSection.tsx << 'FILE_EOF_07'
// src/components/form/FinancialSection.tsx
import { useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AnalyzeRequest } from "@/types/request";

const FIELDS = [
  { key: "income" as const, label: "Monthly income (USD)" },
  { key: "expenses" as const, label: "Monthly expenses (USD)" },
  { key: "monthly_debt" as const, label: "Monthly debt payments (USD)" },
  { key: "savings" as const, label: "Total savings (USD)" },
];

export function FinancialSection() {
  const { register } = useFormContext<AnalyzeRequest>();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {FIELDS.map(({ key, label }) => (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-sm font-medium">
            {label}
          </Label>
          <Input
            id={key}
            type="number"
            min={0}
            step={100}
            {...register(`user.financial.${key}`, { valueAsNumber: true })}
          />
        </div>
      ))}
    </div>
  );
}
FILE_EOF_07

echo "[8/21] Writing src/components/form/ProfessionalSection.tsx..."
cat > frontend-react/src/components/form/ProfessionalSection.tsx << 'FILE_EOF_08'
// src/components/form/ProfessionalSection.tsx
import { useFormContext, useWatch, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Check } from "@phosphor-icons/react";
import type { AnalyzeRequest } from "@/types/request";

interface Props {
  sectors?: string[];
  professionsBySector?: Record<string, string[]>;
  interests?: string[];
  employmentStatuses?: string[];
  weeklyHours?: string[];
}

const HOURS_LABELS: Record<string, string> = {
  "0-5": "0-5h/week (passive)",
  "5-15": "5-15h/week (light)",
  "15-30": "15-30h/week (moderate)",
  "30+": "30+h/week (full-time)",
};

const FALLBACK_INTERESTS = [
  "fitness", "running", "cooking", "programming", "technology",
  "investing", "real estate", "travel", "reading", "music",
];

const FALLBACK_SECTORS = ["Technology", "Healthcare", "Finance", "Other"];

const FALLBACK_EMPLOYMENT = [
  "full-time", "part-time", "freelancer", "self-employed",
  "unemployed", "student", "retired",
];

const FALLBACK_HOURS = ["0-5", "5-15", "15-30", "30+"];

export function ProfessionalSection({
  sectors,
  professionsBySector,
  interests,
  employmentStatuses,
  weeklyHours,
}: Props) {
  const { register, control, setValue } = useFormContext<AnalyzeRequest>();
  const selectedSector = useWatch({ control, name: "user.professional.sector" });
  const currentInterests = useWatch({ control, name: "user.professional.interests" }) ?? [];

  // Defensive defaults
  const safeSectors = (sectors && sectors.length > 0) ? sectors : FALLBACK_SECTORS;
  const safeProfessionsBySector = professionsBySector ?? {};
  const safeInterests = (interests && interests.length > 0) ? interests : FALLBACK_INTERESTS;
  const safeEmployment = (employmentStatuses && employmentStatuses.length > 0) ? employmentStatuses : FALLBACK_EMPLOYMENT;
  const safeHours = (weeklyHours && weeklyHours.length > 0) ? weeklyHours : FALLBACK_HOURS;
  const professions = safeProfessionsBySector[selectedSector] ?? [];

  const toggleInterest = (interest: string) => {
    const current = currentInterests as string[];
    if (current.includes(interest)) {
      setValue("user.professional.interests", current.filter((i) => i !== interest));
    } else if (current.length < 4) {
      setValue("user.professional.interests", [...current, interest]);
    }
  };

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Sector */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Sector</Label>
          <Controller
            control={control}
            name="user.professional.sector"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(v) => {
                  field.onChange(v);
                  const first = safeProfessionsBySector[v]?.[0] ?? "";
                  setValue("user.professional.profession", first);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select sector" />
                </SelectTrigger>
                <SelectContent className="max-h-72">
                  {safeSectors.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>

        {/* Profession */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Profession</Label>
          <Controller
            control={control}
            name="user.professional.profession"
            render={({ field }) => (
              professions.length > 0 ? (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select profession" />
                  </SelectTrigger>
                  <SelectContent className="max-h-72">
                    {professions.map((p) => (
                      <SelectItem key={p} value={p}>{p}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input placeholder="Enter profession" {...field} />
              )
            )}
          />
        </div>

        {/* Employment status */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Employment status</Label>
          <Controller
            control={control}
            name="user.professional.employment_status"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {safeEmployment.map((e) => (
                    <SelectItem key={e} value={e}>{e}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>

        {/* Weekly hours */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Weekly hours available</Label>
          <Controller
            control={control}
            name="user.professional.weekly_hours"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {safeHours.map((h) => (
                    <SelectItem key={h} value={h}>{HOURS_LABELS[h] ?? h}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      {/* Prior experience */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">Prior experience (optional)</Label>
        <Textarea
          rows={2}
          placeholder="E.g., 'Built 2 side projects', 'ETF investing for 5 years'..."
          {...register("user.professional.prior_experience")}
        />
      </div>

      {/* Interests — chip-style selectable */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-sm font-medium">
            Interests
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              (Select up to 4 — used to personalize recommendations)
            </span>
          </Label>
          <Badge variant={currentInterests.length === 4 ? "default" : "outline"}>
            {currentInterests.length} / 4
          </Badge>
        </div>

        <div className="flex flex-wrap gap-2">
          {safeInterests.map((interest) => {
            const checked = (currentInterests as string[]).includes(interest);
            const disabled = !checked && (currentInterests as string[]).length >= 4;
            return (
              <button
                key={interest}
                type="button"
                disabled={disabled}
                onClick={() => toggleInterest(interest)}
                className={`
                  inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
                  text-xs font-medium transition-all border
                  ${checked
                    ? "bg-primary text-primary-foreground border-primary shadow-sm"
                    : disabled
                      ? "bg-muted text-muted-foreground border-border opacity-50 cursor-not-allowed"
                      : "bg-background text-foreground border-border hover:border-primary hover:bg-primary/5 cursor-pointer"
                  }
                `}
              >
                {checked && <Check weight="bold" className="h-3 w-3" />}
                <span className="capitalize">{interest}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
FILE_EOF_08

echo "[9/21] Writing src/components/form/PreferencesSection.tsx..."
cat > frontend-react/src/components/form/PreferencesSection.tsx << 'FILE_EOF_09'
// src/components/form/PreferencesSection.tsx
import { useFormContext, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import type { AnalyzeRequest } from "@/types/request";

interface Props {
  riskProfiles?: string[];
  horizons?: string[];
}

const RISK_LABELS: Record<string, string> = {
  low: "Low — capital preservation",
  medium: "Medium — balanced growth",
  high: "High — aggressive growth",
};

const HORIZON_LABELS: Record<string, string> = {
  "1-3": "1-3 years (short term)",
  "3-5": "3-5 years (medium)",
  "5-8": "5-8 years (long)",
  "8+": "8+ years (very long)",
};

const FALLBACK_RISKS = ["low", "medium", "high"];
const FALLBACK_HORIZONS = ["1-3", "3-5", "5-8", "8+"];

export function PreferencesSection({ riskProfiles, horizons }: Props) {
  const { control } = useFormContext<AnalyzeRequest>();

  const safeRisks = (riskProfiles && riskProfiles.length > 0) ? riskProfiles : FALLBACK_RISKS;
  const safeHorizons = (horizons && horizons.length > 0) ? horizons : FALLBACK_HORIZONS;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label className="text-sm font-medium">Risk tolerance</Label>
        <Controller
          control={control}
          name="user.preferences.risk_profile"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {safeRisks.map((r) => (
                  <SelectItem key={r} value={r}>{RISK_LABELS[r] ?? r}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="space-y-2">
        <Label className="text-sm font-medium">Investment horizon</Label>
        <Controller
          control={control}
          name="user.preferences.horizon"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {safeHorizons.map((h) => (
                  <SelectItem key={h} value={h}>{HORIZON_LABELS[h] ?? h}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>
    </div>
  );
}
FILE_EOF_09

echo "[10/21] Writing src/components/form/StrategiesSection.tsx..."
cat > frontend-react/src/components/form/StrategiesSection.tsx << 'FILE_EOF_10'
// src/components/form/StrategiesSection.tsx
import { useFormContext, useWatch } from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Buildings, House, ChartLine } from "@phosphor-icons/react";
import type { AnalyzeRequest } from "@/types/request";

const STRATEGIES = [
  {
    key: "business" as const,
    title: "Business",
    icon: Buildings,
    description: "Start or fund a side business (SaaS, e-commerce, services, passive income).",
    color: "text-blue-500",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  {
    key: "real_estate" as const,
    title: "Real Estate",
    icon: House,
    description: "Direct property purchase with mortgage (rental, flip, commercial).",
    color: "text-emerald-500",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
  },
  {
    key: "stock" as const,
    title: "Stocks / ETFs",
    icon: ChartLine,
    description: "Stock portfolio (ETFs, dividend, REITs, optional margin).",
    color: "text-orange-500",
    bg: "bg-orange-50",
    border: "border-orange-200",
  },
];

export function StrategiesSection() {
  const { register, control } = useFormContext<AnalyzeRequest>();
  const config = useWatch({ control, name: "config" });

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-2">Configure each strategy</h2>
        <p className="text-sm text-muted-foreground">
          Specify how much to borrow and how much of your savings to use for each.
          Set loan amount to <code className="bg-muted px-1.5 py-0.5 rounded text-xs">0</code> to disable a strategy.
        </p>
      </div>

      {STRATEGIES.map(({ key, title, icon: Icon, description, color, bg, border }) => {
        const cfg = config?.[key];
        const total = (cfg?.loan_amount ?? 0) + (cfg?.savings_to_use ?? 0);
        const disabled = (cfg?.loan_amount ?? 0) === 0 && (cfg?.savings_to_use ?? 0) === 0;

        return (
          <Card key={key} className={disabled ? "opacity-60" : ""}>
            <CardHeader className={`${bg} ${border} border-b`}>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Icon weight="duotone" className={`h-5 w-5 ${color}`} />
                    {title}
                  </CardTitle>
                  <CardDescription className="mt-1 text-xs">{description}</CardDescription>
                </div>
                {!disabled && total > 0 && (
                  <Badge variant="outline" className="text-xs">
                    ${total.toLocaleString()} total
                  </Badge>
                )}
                {disabled && (
                  <Badge variant="secondary" className="text-xs">Disabled</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs">Loan amount (USD)</Label>
                  <Input
                    type="number"
                    min={0}
                    step={1000}
                    {...register(`config.${key}.loan_amount`, { valueAsNumber: true })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Loan years</Label>
                  <Input
                    type="number"
                    min={0}
                    max={40}
                    {...register(`config.${key}.loan_years`, { valueAsNumber: true })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Savings to use (USD)</Label>
                  <Input
                    type="number"
                    min={0}
                    step={1000}
                    {...register(`config.${key}.savings_to_use`, { valueAsNumber: true })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">
                    Interest rate <span className="text-muted-foreground">(0.055 = 5.5%)</span>
                  </Label>
                  <Input
                    type="number"
                    min={0}
                    max={1}
                    step={0.001}
                    {...register(`config.${key}.interest_rate`, { valueAsNumber: true })}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
FILE_EOF_10

echo "[11/21] Writing src/components/charts/ReturnComparisonBar.tsx..."
cat > frontend-react/src/components/charts/ReturnComparisonBar.tsx << 'FILE_EOF_11'
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
FILE_EOF_11

echo "[12/21] Writing src/components/charts/CashflowLineChart.tsx..."
cat > frontend-react/src/components/charts/CashflowLineChart.tsx << 'FILE_EOF_12'
// src/components/charts/CashflowLineChart.tsx
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import type { CashflowChart } from "@/types/response";

interface Props {
  data: CashflowChart;
}

export function CashflowLineChart({ data }: Props) {
  // Transform: from series[].data into rows [{year, RE, Stocks, Business}]
  const chartData = data.categories.map((cat, idx) => {
    const row: Record<string, string | number> = { year: cat };
    data.series.forEach((s) => {
      row[s.name] = s.data[idx];
    });
    return row;
  });

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 16, right: 20, left: 12, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
            axisLine={{ stroke: "hsl(var(--border))" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            axisLine={{ stroke: "hsl(var(--border))" }}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              fontSize: "12px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            }}
            formatter={(value: number) => [`$${value.toLocaleString()}`, ""]}
          />
          <Legend
            wrapperStyle={{ fontSize: "12px" }}
            iconType="circle"
          />
          {data.series.map((s) => (
            <Line
              key={s.name}
              type="monotone"
              dataKey={s.name}
              stroke={s.color}
              strokeWidth={2.5}
              dot={{ r: 5, strokeWidth: 2, fill: "white" }}
              activeDot={{ r: 7 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
FILE_EOF_12

echo "[13/21] Writing src/components/charts/RiskScatter.tsx..."
cat > frontend-react/src/components/charts/RiskScatter.tsx << 'FILE_EOF_13'
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
FILE_EOF_13

echo "[14/21] Writing src/components/charts/BreakEvenBar.tsx..."
cat > frontend-react/src/components/charts/BreakEvenBar.tsx << 'FILE_EOF_14'
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
FILE_EOF_14

echo "[15/21] Writing src/components/charts/AllocationDonut.tsx..."
cat > frontend-react/src/components/charts/AllocationDonut.tsx << 'FILE_EOF_15'
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
FILE_EOF_15

echo "[16/21] Writing src/components/charts/ScenariosBar.tsx..."
cat > frontend-react/src/components/charts/ScenariosBar.tsx << 'FILE_EOF_16'
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
FILE_EOF_16

echo "[17/21] Writing src/components/strategy/CalculationBreakdown.tsx..."
cat > frontend-react/src/components/strategy/CalculationBreakdown.tsx << 'FILE_EOF_17'
// src/components/strategy/CalculationBreakdown.tsx
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CaretDown, CaretUp, Calculator } from "@phosphor-icons/react";
import type { CalcBreakdown } from "@/types/response";

interface Props {
  breakdown: CalcBreakdown;
}

export function CalculationBreakdown({ breakdown }: Props) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Calculator weight="duotone" className="h-5 w-5 text-primary" />
          Calculation Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {breakdown.steps.map((step) => {
          const isExpanded = expandedStep === step.step;
          return (
            <div
              key={step.step}
              className={`
                border rounded-lg overflow-hidden transition-all
                ${isExpanded ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}
              `}
            >
              <button
                type="button"
                onClick={() => setExpandedStep(isExpanded ? null : step.step)}
                className="w-full flex items-center justify-between p-3 text-left"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <Badge variant="outline" className="shrink-0 tabular-nums">
                    Step {step.step}
                  </Badge>
                  <span className="font-medium text-sm truncate">{step.title}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-primary font-semibold whitespace-nowrap">
                    {step.result.split(" ")[0]}
                  </span>
                  {isExpanded ? <CaretUp className="h-4 w-4" /> : <CaretDown className="h-4 w-4" />}
                </div>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 pt-1 space-y-3 animate-fade-in">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {step.explanation}
                  </p>

                  <div className="bg-background border rounded p-2.5 font-mono text-xs">
                    <div className="text-muted-foreground mb-1">Formula:</div>
                    <div className="text-foreground">{step.formula}</div>
                  </div>

                  <div className="flex items-baseline justify-between">
                    <span className="text-xs text-muted-foreground">Result:</span>
                    <span className="font-mono font-semibold text-primary">{step.result}</span>
                  </div>

                  {step.note && (
                    <div className="bg-amber-50 border border-amber-200 rounded p-2 text-xs text-amber-900">
                      {step.note}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Conclusion */}
        {breakdown.conclusion && (
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <h4 className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wide">
              Conclusion
            </h4>
            <p className="text-sm whitespace-pre-wrap leading-relaxed">
              {breakdown.conclusion}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
FILE_EOF_17

echo "[18/21] Writing src/components/strategy/PortfolioComposition.tsx..."
cat > frontend-react/src/components/strategy/PortfolioComposition.tsx << 'FILE_EOF_18'
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
FILE_EOF_18

echo "[19/21] Writing src/components/strategy/StrategyDetailCard.tsx..."
cat > frontend-react/src/components/strategy/StrategyDetailCard.tsx << 'FILE_EOF_19'
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
FILE_EOF_19

echo "[20/21] Writing src/pages/FormPage.tsx..."
cat > frontend-react/src/pages/FormPage.tsx << 'FILE_EOF_20'
// src/pages/FormPage.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm, FormProvider } from "react-hook-form";
import { useOptions } from "@/hooks/useOptions";
import { useAnalyze } from "@/hooks/useAnalyze";
import { DEMO_PROFILES, type DemoProfileKey } from "@/lib/defaults";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { AnalyzeRequest } from "@/types/request";
import { PersonalSection } from "@/components/form/PersonalSection";
import { LocationSection } from "@/components/form/LocationSection";
import { FinancialSection } from "@/components/form/FinancialSection";
import { ProfessionalSection } from "@/components/form/ProfessionalSection";
import { PreferencesSection } from "@/components/form/PreferencesSection";
import { StrategiesSection } from "@/components/form/StrategiesSection";
import {
  Lightning, MapPin, Briefcase, CurrencyDollar, ChartLine,
  Sparkle, User, Gear, Truck, Stethoscope, Code
} from "@phosphor-icons/react";

const PROFILE_ICONS = {
  truck_driver: Truck,
  doctor: Stethoscope,
  engineer: Code,
};

export function FormPage() {
  const navigate = useNavigate();
  const optionsQuery = useOptions();
  const analyzeMutation = useAnalyze();
  const [activeTab, setActiveTab] = useState("profile");

  const methods = useForm<AnalyzeRequest>({
    defaultValues: DEMO_PROFILES.truck_driver.data,
    mode: "onChange",
  });

  const loadDemo = (key: DemoProfileKey) => {
    methods.reset(DEMO_PROFILES[key].data);
  };

  const onSubmit = async (data: AnalyzeRequest) => {
    try {
      const result = await analyzeMutation.mutateAsync(data);
      sessionStorage.setItem("analysis_result", JSON.stringify(result));
      sessionStorage.setItem("analysis_input", JSON.stringify(data));
      navigate("/results");
    } catch (error) {
      console.error("Submit failed:", error);
    }
  };

  // Loading
  if (optionsQuery.isLoading) {
    return (
      <div className="container mx-auto py-8 max-w-5xl px-4 space-y-4">
        <Skeleton className="h-12 w-1/3" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  // Error
  if (optionsQuery.isError) {
    return (
      <div className="container mx-auto py-8 max-w-3xl px-4">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Cannot reach backend</CardTitle>
            <CardDescription>
              Make sure FastAPI is running on{" "}
              <code className="bg-muted px-2 py-0.5 rounded text-xs">http://localhost:8000</code>
              <br />
              Try: <code className="bg-muted px-2 py-0.5 rounded text-xs">make backend</code>
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const options = optionsQuery.data!;

  return (
    <div className="container mx-auto py-6 max-w-5xl px-4 animate-fade-in">
      {/* HEADER */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
            <Sparkle weight="duotone" className="text-primary h-9 w-9" />
            CaliforniaCFO
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            AI-powered investment advisor for California residents
          </p>
        </div>
        <Badge variant="outline" className="text-xs">v5.2.5</Badge>
      </div>

      {/* DEMO PROFILES */}
      <Card className="mb-6 border-dashed bg-muted/30">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Lightning weight="fill" className="text-yellow-500 h-4 w-4" />
            Quick start — Load a demo profile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {(Object.keys(DEMO_PROFILES) as DemoProfileKey[]).map((key) => {
              const Icon = PROFILE_ICONS[key];
              return (
                <Button
                  key={key}
                  variant="outline"
                  size="sm"
                  onClick={() => loadDemo(key)}
                  type="button"
                  className="gap-2"
                >
                  <Icon weight="duotone" className="h-4 w-4" />
                  {DEMO_PROFILES[key].label}
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* MAIN FORM */}
      <FormProvider {...methods}>
        <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="profile" className="gap-2">
                <User weight="duotone" className="h-4 w-4" />
                Your Profile
              </TabsTrigger>
              <TabsTrigger value="strategies" className="gap-2">
                <Gear weight="duotone" className="h-4 w-4" />
                Strategies Setup
              </TabsTrigger>
            </TabsList>

            {/* TAB 1: PROFILE */}
            <TabsContent value="profile" className="space-y-4 animate-fade-in">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <User className="h-5 w-5 text-primary" weight="duotone" />
                    Personal
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <PersonalSection />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <MapPin className="h-5 w-5 text-primary" weight="duotone" />
                    Location
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <LocationSection
                    regions={options.regions}
                    citiesByRegion={options.cities_by_region}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <CurrencyDollar className="h-5 w-5 text-primary" weight="duotone" />
                    Financial Snapshot
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FinancialSection />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Briefcase className="h-5 w-5 text-primary" weight="duotone" />
                    Professional Background
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ProfessionalSection
                    sectors={options.sectors}
                    professionsBySector={options.professions_by_sector}
                    interests={options.predefined_interests}
                    employmentStatuses={options.employment_statuses}
                    weeklyHours={options.weekly_hours}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Preferences</CardTitle>
                </CardHeader>
                <CardContent>
                  <PreferencesSection
                    riskProfiles={options.risk_profiles}
                    horizons={options.horizons}
                  />
                </CardContent>
              </Card>

              <div className="flex justify-end">
                <Button
                  type="button"
                  onClick={() => setActiveTab("strategies")}
                  size="lg"
                  className="gap-2"
                >
                  Continue to Strategies
                  <ChartLine weight="duotone" className="h-4 w-4" />
                </Button>
              </div>
            </TabsContent>

            {/* TAB 2: STRATEGIES */}
            <TabsContent value="strategies" className="space-y-4 animate-fade-in">
              <StrategiesSection />

              <Separator className="my-4" />

              <div className="flex justify-between items-center">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setActiveTab("profile")}
                  className="gap-2"
                >
                  ← Back to Profile
                </Button>
                <Button
                  type="submit"
                  size="lg"
                  disabled={analyzeMutation.isPending}
                  className="min-w-[220px] gap-2"
                >
                  {analyzeMutation.isPending ? (
                    <>
                      <span className="animate-spin">⏳</span>
                      Analyzing… (~30s)
                    </>
                  ) : (
                    <>
                      <Sparkle weight="fill" className="h-4 w-4" />
                      Get AI Recommendations
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </form>
      </FormProvider>
    </div>
  );
}
FILE_EOF_20

echo "[21/21] Writing src/pages/ResultsPage.tsx..."
cat > frontend-react/src/pages/ResultsPage.tsx << 'FILE_EOF_21'
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
FILE_EOF_21

echo ""
echo "✅ All Day 2 files installed!"
echo ""
echo "Next steps:"
echo "  1. cd frontend-react && npm install @fontsource-variable/geist @fontsource-variable/geist-mono"
echo "  2. Restart Vite (Ctrl+C in frontend terminal, then make frontend)"
echo "  3. Hard refresh browser (Ctrl+Shift+R)"
echo "  4. Click any demo profile + Submit"
