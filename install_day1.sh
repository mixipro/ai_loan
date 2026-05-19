#!/bin/bash
# ═══════════════════════════════════════════════════════════
# CaliforniaCFO Day 1 — Install all React files at once
# ═══════════════════════════════════════════════════════════
# Run from project root: ~/PycharmProjects/ai_loan
# Usage:                 bash install_day1.sh
# ═══════════════════════════════════════════════════════════

set -e

# Verify we're in project root
if [ ! -d "frontend-react" ]; then
    echo "❌ ERROR: frontend-react/ folder not found"
    echo "   Run this from: ~/PycharmProjects/ai_loan"
    exit 1
fi

echo "📁 Creating folders..."
mkdir -p frontend-react/src/types
mkdir -p frontend-react/src/hooks
mkdir -p frontend-react/src/pages
mkdir -p frontend-react/src/components/form
echo "✓ Folders created"

echo "[1/18] Writing vite.config.ts..."
cat > frontend-react/vite.config.ts << 'FILE_EOF_01'
import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy /api/* requests to FastAPI backend on :8000
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
})
FILE_EOF_01

echo "[2/18] Writing src/types/options.ts..."
cat > frontend-react/src/types/options.ts << 'FILE_EOF_02'
// src/types/options.ts
// Types for GET /options endpoint response

export interface RegionOption {
  value: string;          // "BAY_AREA", "LOS_ANGELES", etc.
  label: string;          // "Bay Area", "Los Angeles"
  description: string;
  primary_industries: string[];
}

export interface SectorOption {
  value: string;          // "Technology", "Healthcare", etc.
  label: string;
}

export interface CityOption {
  value: string;
  label: string;
  region: string;
}

export interface OptionsResponse {
  regions: RegionOption[];
  sectors: SectorOption[];
  cities_by_region: Record<string, string[]>;
  professions_by_sector: Record<string, string[]>;
  interests: string[];
  weekly_hours: string[];
  risk_profiles: string[];
  horizons: string[];
  employment_statuses: string[];
}
FILE_EOF_02

echo "[3/18] Writing src/types/request.ts..."
cat > frontend-react/src/types/request.ts << 'FILE_EOF_03'
// src/types/request.ts
// Types for POST /analyze request body

export type WeeklyHours = "0-5" | "5-15" | "15-30" | "30+";
export type RiskProfile = "low" | "medium" | "high";
export type Horizon = "1-3" | "3-5" | "5-8" | "8+";
export type Currency = "USD";
export type EmploymentStatus =
  | "full-time"
  | "part-time"
  | "freelancer"
  | "self-employed"
  | "unemployed"
  | "student"
  | "retired";

export interface PersonalInfo {
  age: number;
}

export interface LocationInfo {
  region: string;         // "BAY_AREA", "LOS_ANGELES", etc.
  city: string;
}

export interface FinancialInfo {
  income: number;
  expenses: number;
  monthly_debt: number;
  savings: number;
  currency: Currency;
}

export interface ProfessionalInfo {
  sector: string;
  profession: string;
  employment_status: EmploymentStatus;
  interests: string[];        // max 4
  prior_experience: string;
  weekly_hours: WeeklyHours;
}

export interface Preferences {
  risk_profile: RiskProfile;
  horizon: Horizon;
}

export interface UserInput {
  personal: PersonalInfo;
  location: LocationInfo;
  financial: FinancialInfo;
  professional: ProfessionalInfo;
  preferences: Preferences;
}

export interface StrategyConfig {
  loan_amount: number;
  loan_years: number;
  savings_to_use: number;
  interest_rate: number;
}

export interface AnalysisConfig {
  business: StrategyConfig;
  real_estate: StrategyConfig;
  stock: StrategyConfig;
}

export interface AnalyzeRequest {
  user: UserInput;
  config: AnalysisConfig;
}
FILE_EOF_03

echo "[4/18] Writing src/types/response.ts..."
cat > frontend-react/src/types/response.ts << 'FILE_EOF_04'
// src/types/response.ts
// Types for POST /analyze response

export type AgentName = "business" | "real_estate" | "stock";
export type FundingMode = "cash" | "loan" | "mixed" | "mortgage" | "margin" | "rejected";
export type Status = "profitable" | "marginal" | "not_profitable" | "?";

// ───── Allocation (different per agent) ─────
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

export type Allocation =
  | BusinessAllocation
  | RealEstateAllocation
  | StockAllocation
  | Record<string, number>;

// ───── Projections (Y1/Y3/Y5) ─────
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
  margin_interest?: number;
  ca_capital_gains_tax: number;
  net_return: number;
}

export interface Projections<T> {
  year_1: T;
  year_3: T;
  year_5: T;
}

// ───── Scenarios ─────
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
  price_change_pct: number;
  dividend_pct: number;
  total_return_pct: number;
  narrative: string;
}

export interface Scenarios<T> {
  best_case: T;
  base_case: T;
  worst_case: T;
}

// ───── Break Even ─────
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

// ───── Calculation Breakdown ─────
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

// ───── Unit Economics (Business) ─────
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

// ───── Market Context ─────
export interface BusinessMarketContext {
  industry_growth_rate_pct: number;
  key_competitors: string[];
  market_size_local_usd: number;
  demand_indicator: string;
}

export interface RealEstateMarketContext {
  median_property_value_usd: number;
  median_rent_monthly_usd: number;
  rent_to_price_ratio_pct: number;
  appreciation_rate_pct_5yr: number;
  comparable_properties: string[];
  demand_indicator: string;
}

// ───── Property Economics (RE only) ─────
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

// ───── Loan Info ─────
export interface LoanInfo {
  type: string;
  amount: number;
  rate: number;
  years: number;
  annual_payment: number;
}

// ───── BASE STRATEGY ─────
interface BaseStrategy {
  agent: AgentName;
  title: string;
  type: string;
  description: string;
  allocation: Allocation;
  expected_return: number;
  risk: number;
  stability: number;
  pros: string[];
  cons: string[];
  next_steps: string[];
  time_to_profit: string;

  // Engine metadata
  funding_mode: FundingMode;
  loan_amount: number;
  loan_years: number;
  savings_used: number;
  interest_rate: number;
  total_capital: number;
  annual_payment?: number;
  loan_info?: LoanInfo;

  // Computed values
  nominal_return: number;
  real_return: number;
  net_return: number;
  net_return_dollars: number;
  gross_return_dollars: number;
  status: Status;
  derived_status_override?: string;
  personalized_score: number;
  score?: number;

  // Sources & extras
  rag_sources: string[];
  calculation_breakdown: CalcBreakdown;

  // Rejection
  rejected: boolean;
  rejection_reason?: string;
}

// ───── BUSINESS ─────
export interface BusinessStrategy extends BaseStrategy {
  agent: "business";
  market_context: BusinessMarketContext;
  unit_economics: UnitEconomics;
  projections: Projections<BusinessProjection>;
  scenarios: Scenarios<BusinessScenario>;
  break_even: BusinessBreakEven;
}

// ───── REAL ESTATE ─────
export interface RealEstateStrategy extends BaseStrategy {
  agent: "real_estate";
  property_market_context: RealEstateMarketContext;
  property_economics: PropertyEconomics;
  projections: Projections<RealEstateProjection>;
  scenarios: Scenarios<RealEstateScenario>;
  break_even: RealEstateBreakEven;
  down_payment_pct: number;
}

// ───── STOCK ─────
export interface StockStrategy extends BaseStrategy {
  agent: "stock";
  market_context: BusinessMarketContext;
  portfolio_composition?: Record<string, number>;
  projections: Projections<StockProjection>;
  scenarios: Scenarios<StockScenario>;
  margin_call_risk?: { probability: number; severity: number };
}

export type Strategy = BusinessStrategy | RealEstateStrategy | StockStrategy;

// ───── JUDGE / RECOMMENDATION ─────
export interface Recommendation {
  winner_agent: AgentName;
  title: string;
  reasoning: string;
  comparison: string;
  risk_analysis: string;
  california_angle: string;
  action_plan: string[];
}

// ───── COMPARISON CHARTS DATA ─────
export interface ComparisonCharts {
  net_return_comparison: Array<{ name: string; value: number }>;
  status_comparison: Array<{ name: string; status: Status }>;
  capital_distribution: Array<{ name: string; value: number }>;
  year3_projection: Array<{ name: string; value: number }>;
}

// ───── FULL RESPONSE ─────
export interface AnalyzeResponse {
  user_summary: string;
  risk: string;
  config: Record<string, unknown>;
  loans: Record<string, unknown>;
  strategies: Strategy[];
  recommendation: Recommendation | string;
  reasoning: string;
  next_step: string;
  comparison: string;
  profile_used: string;
  rejected_count: number;
  detailed_explanation?: Record<string, unknown>;
  comparison_charts?: ComparisonCharts;
}
FILE_EOF_04

echo "[5/18] Writing src/lib/api.ts..."
cat > frontend-react/src/lib/api.ts << 'FILE_EOF_05'
// src/lib/api.ts
import axios from "axios";
import type { OptionsResponse } from "@/types/options";
import type { AnalyzeRequest } from "@/types/request";
import type { AnalyzeResponse } from "@/types/response";

// Vite proxy: /api/* → http://localhost:8000/*
const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000, // 2 min — LLM može da bude spor
});

// ───── ENDPOINTS ─────

export async function fetchOptions(): Promise<OptionsResponse> {
  const { data } = await api.get<OptionsResponse>("/options");
  return data;
}

export async function postAnalyze(body: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>("/analyze", body);
  return data;
}

// ───── ERROR HANDLER ─────

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.data) {
      const data = error.response.data;
      if (typeof data === "string") return data;
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          return data.detail
            .map((e: { loc?: string[]; msg?: string }) =>
              `${e.loc?.join(".")}: ${e.msg}`
            )
            .join("; ");
        }
        return String(data.detail);
      }
      return JSON.stringify(data);
    }
    return error.message;
  }
  return error instanceof Error ? error.message : "Unknown error";
}

export default api;
FILE_EOF_05

echo "[6/18] Writing src/lib/defaults.ts..."
cat > frontend-react/src/lib/defaults.ts << 'FILE_EOF_06'
// src/lib/defaults.ts
import type { AnalyzeRequest } from "@/types/request";

/**
 * Truck Driver default profile — used for quick QA testing.
 * Click "Load Demo Profile" in form to apply these.
 */
export const TRUCK_DRIVER_DEFAULTS: AnalyzeRequest = {
  user: {
    personal: { age: 42 },
    location: { region: "SAN_DIEGO", city: "Chula Vista" },
    financial: {
      income: 5500,
      expenses: 3500,
      monthly_debt: 800,
      savings: 120000,
      currency: "USD",
    },
    professional: {
      sector: "Other",
      profession: "Truck Driver",
      employment_status: "full-time",
      interests: ["real estate", "investing"],
      prior_experience: "No business experience",
      weekly_hours: "0-5",
    },
    preferences: {
      risk_profile: "medium",
      horizon: "5-8",
    },
  },
  config: {
    business: {
      loan_amount: 80000,
      loan_years: 7,
      savings_to_use: 40000,
      interest_rate: 0.07,
    },
    real_estate: {
      loan_amount: 320000,
      loan_years: 30,
      savings_to_use: 80000,
      interest_rate: 0.055,
    },
    stock: {
      loan_amount: 0,
      loan_years: 0,
      savings_to_use: 65500,
      interest_rate: 0,
    },
  },
};

export const DOCTOR_DEFAULTS: AnalyzeRequest = {
  user: {
    personal: { age: 38 },
    location: { region: "BAY_AREA", city: "Palo Alto" },
    financial: {
      income: 35000,
      expenses: 12000,
      monthly_debt: 2000,
      savings: 600000,
      currency: "USD",
    },
    professional: {
      sector: "Healthcare",
      profession: "Physician",
      employment_status: "full-time",
      interests: ["technology", "real estate", "investing"],
      prior_experience: "Investing in index funds for 10 years",
      weekly_hours: "5-15",
    },
    preferences: {
      risk_profile: "low",
      horizon: "8+",
    },
  },
  config: {
    business: {
      loan_amount: 150000,
      loan_years: 7,
      savings_to_use: 150000,
      interest_rate: 0.075,
    },
    real_estate: {
      loan_amount: 700000,
      loan_years: 30,
      savings_to_use: 200000,
      interest_rate: 0.058,
    },
    stock: {
      loan_amount: 0,
      loan_years: 0,
      savings_to_use: 250000,
      interest_rate: 0,
    },
  },
};

export const ENGINEER_DEFAULTS: AnalyzeRequest = {
  user: {
    personal: { age: 28 },
    location: { region: "BAY_AREA", city: "San Francisco" },
    financial: {
      income: 12000,
      expenses: 6000,
      monthly_debt: 1500,
      savings: 80000,
      currency: "USD",
    },
    professional: {
      sector: "Technology",
      profession: "Software Engineer",
      employment_status: "full-time",
      interests: ["technology", "ai/ml", "startups", "investing"],
      prior_experience: "Built 3 side projects, ETF investing for 5 years",
      weekly_hours: "30+",
    },
    preferences: {
      risk_profile: "high",
      horizon: "5-8",
    },
  },
  config: {
    business: {
      loan_amount: 60000,
      loan_years: 5,
      savings_to_use: 30000,
      interest_rate: 0.085,
    },
    real_estate: {
      loan_amount: 0,
      loan_years: 0,
      savings_to_use: 0,
      interest_rate: 0,
    },
    stock: {
      loan_amount: 50000,
      loan_years: 5,
      savings_to_use: 50000,
      interest_rate: 0.08,
    },
  },
};

export const DEMO_PROFILES = {
  truck_driver: { label: "Truck Driver (SD, 0-5h)", data: TRUCK_DRIVER_DEFAULTS },
  doctor: { label: "Doctor (Bay Area, 5-15h)", data: DOCTOR_DEFAULTS },
  engineer: { label: "SW Engineer (SF, 30+h)", data: ENGINEER_DEFAULTS },
} as const;

export type DemoProfileKey = keyof typeof DEMO_PROFILES;
FILE_EOF_06

echo "[7/18] Writing src/hooks/useOptions.ts..."
cat > frontend-react/src/hooks/useOptions.ts << 'FILE_EOF_07'
// src/hooks/useOptions.ts
import { useQuery } from "@tanstack/react-query";
import { fetchOptions } from "@/lib/api";

export function useOptions() {
  return useQuery({
    queryKey: ["options"],
    queryFn: fetchOptions,
    staleTime: 1000 * 60 * 60, // 1h cache
  });
}
FILE_EOF_07

echo "[8/18] Writing src/hooks/useAnalyze.ts..."
cat > frontend-react/src/hooks/useAnalyze.ts << 'FILE_EOF_08'
// src/hooks/useAnalyze.ts
import { useMutation } from "@tanstack/react-query";
import { postAnalyze, getErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import type { AnalyzeRequest } from "@/types/request";
import type { AnalyzeResponse } from "@/types/response";

export function useAnalyze() {
  return useMutation<AnalyzeResponse, Error, AnalyzeRequest>({
    mutationFn: postAnalyze,
    onError: (error) => {
      const msg = getErrorMessage(error);
      console.error("[useAnalyze] error:", msg);
      toast.error("Analysis failed", { description: msg });
    },
    onSuccess: (data) => {
      const count = data.strategies?.length ?? 0;
      toast.success("Analysis complete", {
        description: `Generated ${count} investment strategies.`,
      });
    },
  });
}
FILE_EOF_08

echo "[9/18] Writing src/main.tsx..."
cat > frontend-react/src/main.tsx << 'FILE_EOF_09'
// src/main.tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App.tsx";
import "@fontsource-variable/jetbrains-mono";
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
FILE_EOF_09

echo "[10/18] Writing src/App.tsx..."
cat > frontend-react/src/App.tsx << 'FILE_EOF_10'
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { FormPage } from "@/pages/FormPage";
import { ResultsPage } from "@/pages/ResultsPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground">
        <Routes>
          <Route path="/" element={<Navigate to="/form" replace />} />
          <Route path="/form" element={<FormPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="*" element={<Navigate to="/form" replace />} />
        </Routes>
        <Toaster richColors position="top-right" />
      </div>
    </BrowserRouter>
  );
}

export default App;
FILE_EOF_10

echo "[11/18] Writing src/pages/FormPage.tsx..."
cat > frontend-react/src/pages/FormPage.tsx << 'FILE_EOF_11'
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
import { Lightning, Buildings, MapPin, Briefcase, CurrencyDollar, ChartLine, Sparkle } from "@phosphor-icons/react";

export function FormPage() {
  const navigate = useNavigate();
  const optionsQuery = useOptions();
  const analyzeMutation = useAnalyze();
  const [activeTab, setActiveTab] = useState("profile");

  // Initialize with truck driver defaults so user can quickly test
  const methods = useForm<AnalyzeRequest>({
    defaultValues: DEMO_PROFILES.truck_driver.data,
    mode: "onChange",
  });

  const loadDemo = (key: DemoProfileKey) => {
    const profile = DEMO_PROFILES[key];
    methods.reset(profile.data);
  };

  const onSubmit = async (data: AnalyzeRequest) => {
    try {
      const result = await analyzeMutation.mutateAsync(data);
      // Store result in sessionStorage and navigate
      sessionStorage.setItem("analysis_result", JSON.stringify(result));
      sessionStorage.setItem("analysis_input", JSON.stringify(data));
      navigate("/results");
    } catch (error) {
      // Error already toasted by useAnalyze
      console.error("Submit failed:", error);
    }
  };

  if (optionsQuery.isLoading) {
    return (
      <div className="container mx-auto py-8 space-y-4">
        <Skeleton className="h-12 w-1/3" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (optionsQuery.isError) {
    return (
      <div className="container mx-auto py-8">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Cannot reach backend</CardTitle>
            <CardDescription>
              Make sure FastAPI is running on http://localhost:8000.
              Try: <code className="bg-muted px-2 py-1 rounded">make backend</code>
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const options = optionsQuery.data!;

  return (
    <div className="container mx-auto py-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
            <Sparkle weight="duotone" className="text-primary" />
            CaliforniaCFO
          </h1>
          <p className="text-muted-foreground mt-2">
            AI-powered investment advisor for California residents
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          v5.2.5
        </Badge>
      </div>

      {/* Demo Profile Loader */}
      <Card className="mb-6 border-dashed">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Lightning weight="fill" className="text-yellow-500" />
            Quick start — Load demo profile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {(Object.keys(DEMO_PROFILES) as DemoProfileKey[]).map((key) => (
              <Button
                key={key}
                variant="outline"
                size="sm"
                onClick={() => loadDemo(key)}
                type="button"
              >
                {DEMO_PROFILES[key].label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Form */}
      <FormProvider {...methods}>
        <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="profile">
                <Briefcase className="mr-2 h-4 w-4" />
                Your Profile
              </TabsTrigger>
              <TabsTrigger value="strategies">
                <ChartLine className="mr-2 h-4 w-4" />
                Strategies Setup
              </TabsTrigger>
            </TabsList>

            {/* TAB 1: PROFILE */}
            <TabsContent value="profile" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Briefcase className="h-5 w-5 text-primary" />
                    Personal Info
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <PersonalSection />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-primary" />
                    Location
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <LocationSection regions={options.regions} citiesByRegion={options.cities_by_region} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CurrencyDollar className="h-5 w-5 text-primary" />
                    Financial Snapshot
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FinancialSection />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Buildings className="h-5 w-5 text-primary" />
                    Professional Background
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ProfessionalSection
                    sectors={options.sectors}
                    professionsBySector={options.professions_by_sector}
                    interests={options.interests}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Preferences</CardTitle>
                </CardHeader>
                <CardContent>
                  <PreferencesSection />
                </CardContent>
              </Card>

              <div className="flex justify-end">
                <Button type="button" onClick={() => setActiveTab("strategies")} size="lg">
                  Continue to Strategies →
                </Button>
              </div>
            </TabsContent>

            {/* TAB 2: STRATEGIES */}
            <TabsContent value="strategies" className="space-y-4">
              <StrategiesSection />

              <Separator className="my-6" />

              <div className="flex justify-between">
                <Button type="button" variant="outline" onClick={() => setActiveTab("profile")}>
                  ← Back to Profile
                </Button>
                <Button
                  type="submit"
                  size="lg"
                  disabled={analyzeMutation.isPending}
                  className="min-w-[200px]"
                >
                  {analyzeMutation.isPending ? (
                    <span className="flex items-center gap-2">
                      <span className="animate-spin">⏳</span>
                      Analyzing... (~30s)
                    </span>
                  ) : (
                    <>
                      <Sparkle className="mr-2 h-4 w-4" weight="fill" />
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
FILE_EOF_11

echo "[12/18] Writing src/pages/ResultsPage.tsx..."
cat > frontend-react/src/pages/ResultsPage.tsx << 'FILE_EOF_12'
// src/pages/ResultsPage.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Trophy } from "@phosphor-icons/react";
import type { AnalyzeResponse, Strategy } from "@/types/response";

export function ResultsPage() {
  const navigate = useNavigate();
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

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

  const recommendation =
    typeof result.recommendation === "object" ? result.recommendation : null;

  return (
    <div className="container mx-auto py-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" onClick={() => navigate("/form")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to form
        </Button>
        <Badge variant="outline">
          {result.strategies?.length ?? 0} strategies generated
        </Badge>
      </div>

      <h1 className="text-3xl font-bold mb-2">Your Investment Analysis</h1>
      <p className="text-muted-foreground mb-8">{result.user_summary}</p>

      {/* Judge Winner Banner */}
      {recommendation && (
        <Card className="mb-8 border-primary border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-2xl">
              <Trophy weight="fill" className="text-yellow-500" />
              Recommended: {recommendation.title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed mb-4">
              {recommendation.reasoning}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Strategy Cards (Day 2 will polish these) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {result.strategies?.map((strategy: Strategy) => (
          <Card key={strategy.agent}>
            <CardHeader>
              <CardTitle className="text-lg capitalize">{strategy.agent}</CardTitle>
              <p className="text-xs text-muted-foreground">{strategy.title}</p>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Status:</span>
                <Badge
                  variant={
                    strategy.status === "profitable"
                      ? "default"
                      : strategy.status === "marginal"
                        ? "secondary"
                        : "destructive"
                  }
                >
                  {strategy.status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span>Net return:</span>
                <span
                  className={
                    strategy.net_return > 0 ? "text-green-600" : "text-red-600"
                  }
                >
                  {(strategy.net_return * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span>Type:</span>
                <Badge variant="outline">{strategy.type}</Badge>
              </div>
              <div className="flex justify-between">
                <span>Capital:</span>
                <span>${strategy.total_capital?.toLocaleString()}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Day 2 placeholder */}
      <Card className="mt-8 border-dashed">
        <CardHeader>
          <CardTitle className="text-muted-foreground">
            🚧 Coming in Day 2:
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-1">
          <p>• Detailed allocation pie charts</p>
          <p>• 5-year projection line charts</p>
          <p>• Best/Base/Worst scenarios bar charts</p>
          <p>• Step-by-step calculation breakdown</p>
          <p>• Pros/Cons & next steps</p>
          <p>• Comparable properties / portfolio composition</p>
        </CardContent>
      </Card>
    </div>
  );
}
FILE_EOF_12

echo "[13/18] Writing src/components/form/PersonalSection.tsx..."
cat > frontend-react/src/components/form/PersonalSection.tsx << 'FILE_EOF_13'
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
        <Label htmlFor="age">Age</Label>
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
FILE_EOF_13

echo "[14/18] Writing src/components/form/LocationSection.tsx..."
cat > frontend-react/src/components/form/LocationSection.tsx << 'FILE_EOF_14'
// src/components/form/LocationSection.tsx
import { useFormContext, useWatch, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import type { AnalyzeRequest } from "@/types/request";
import type { RegionOption } from "@/types/options";

interface Props {
  regions: RegionOption[];
  citiesByRegion: Record<string, string[]>;
}

export function LocationSection({ regions, citiesByRegion }: Props) {
  const { control, setValue } = useFormContext<AnalyzeRequest>();
  const selectedRegion = useWatch({ control, name: "user.location.region" });
  const cities = citiesByRegion[selectedRegion] ?? [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label>Region</Label>
        <Controller
          control={control}
          name="user.location.region"
          render={({ field }) => (
            <Select
              value={field.value}
              onValueChange={(v) => {
                field.onChange(v);
                // Reset city when region changes
                const firstCity = citiesByRegion[v]?.[0] ?? "";
                setValue("user.location.city", firstCity);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a region" />
              </SelectTrigger>
              <SelectContent>
                {regions.map((r) => (
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
        <Label>City</Label>
        <Controller
          control={control}
          name="user.location.city"
          render={({ field }) => (
            cities.length > 0 ? (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a city" />
                </SelectTrigger>
                <SelectContent>
                  {cities.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                  {/* Allow custom city */}
                  <SelectItem value={field.value || "_custom_"}>
                    {field.value || "Custom..."}
                  </SelectItem>
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
FILE_EOF_14

echo "[15/18] Writing src/components/form/FinancialSection.tsx..."
cat > frontend-react/src/components/form/FinancialSection.tsx << 'FILE_EOF_15'
// src/components/form/FinancialSection.tsx
import { useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AnalyzeRequest } from "@/types/request";

export function FinancialSection() {
  const { register } = useFormContext<AnalyzeRequest>();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label htmlFor="income">Monthly income (USD)</Label>
        <Input
          id="income"
          type="number"
          min={0}
          {...register("user.financial.income", { valueAsNumber: true })}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="expenses">Monthly expenses (USD)</Label>
        <Input
          id="expenses"
          type="number"
          min={0}
          {...register("user.financial.expenses", { valueAsNumber: true })}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="debt">Monthly debt payments (USD)</Label>
        <Input
          id="debt"
          type="number"
          min={0}
          {...register("user.financial.monthly_debt", { valueAsNumber: true })}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="savings">Total savings (USD)</Label>
        <Input
          id="savings"
          type="number"
          min={0}
          {...register("user.financial.savings", { valueAsNumber: true })}
        />
      </div>
    </div>
  );
}
FILE_EOF_15

echo "[16/18] Writing src/components/form/ProfessionalSection.tsx..."
cat > frontend-react/src/components/form/ProfessionalSection.tsx << 'FILE_EOF_16'
// src/components/form/ProfessionalSection.tsx
import { useFormContext, useWatch, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import type { AnalyzeRequest } from "@/types/request";
import type { SectorOption } from "@/types/options";

interface Props {
  sectors: SectorOption[];
  professionsBySector: Record<string, string[]>;
  interests: string[];
}

const HOURS_OPTIONS = [
  { value: "0-5", label: "0-5h/week (passive)" },
  { value: "5-15", label: "5-15h/week (light)" },
  { value: "15-30", label: "15-30h/week (moderate)" },
  { value: "30+", label: "30+h/week (full-time)" },
];

const EMPLOYMENT_OPTIONS = [
  "full-time", "part-time", "freelancer", "self-employed",
  "unemployed", "student", "retired",
];

export function ProfessionalSection({ sectors, professionsBySector, interests }: Props) {
  const { register, control, setValue } = useFormContext<AnalyzeRequest>();
  const selectedSector = useWatch({ control, name: "user.professional.sector" });
  const currentInterests = useWatch({ control, name: "user.professional.interests" }) ?? [];

  const professions = professionsBySector[selectedSector] ?? [];

  const toggleInterest = (interest: string) => {
    const current = currentInterests as string[];
    if (current.includes(interest)) {
      setValue("user.professional.interests", current.filter((i) => i !== interest));
    } else if (current.length < 4) {
      setValue("user.professional.interests", [...current, interest]);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Sector</Label>
          <Controller
            control={control}
            name="user.professional.sector"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={(v) => {
                  field.onChange(v);
                  const first = professionsBySector[v]?.[0] ?? "";
                  setValue("user.professional.profession", first);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a sector" />
                </SelectTrigger>
                <SelectContent>
                  {sectors.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>

        <div className="space-y-2">
          <Label>Profession</Label>
          <Controller
            control={control}
            name="user.professional.profession"
            render={({ field }) => (
              professions.length > 0 ? (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a profession" />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {professions.map((p) => (
                      <SelectItem key={p} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input placeholder="Enter profession" {...field} />
              )
            )}
          />
        </div>

        <div className="space-y-2">
          <Label>Employment status</Label>
          <Controller
            control={control}
            name="user.professional.employment_status"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EMPLOYMENT_OPTIONS.map((e) => (
                    <SelectItem key={e} value={e}>{e}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>

        <div className="space-y-2">
          <Label>Weekly hours available</Label>
          <Controller
            control={control}
            name="user.professional.weekly_hours"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {HOURS_OPTIONS.map((h) => (
                    <SelectItem key={h.value} value={h.value}>{h.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Prior experience (optional)</Label>
        <Textarea
          rows={2}
          placeholder="E.g., 'Built 2 side projects', 'ETF investing for 5 years'..."
          {...register("user.professional.prior_experience")}
        />
      </div>

      <div className="space-y-2">
        <Label>
          Interests <span className="text-xs text-muted-foreground">(select up to 4)</span>
        </Label>
        <Badge variant="outline" className="ml-2">
          {currentInterests.length}/4 selected
        </Badge>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
          {interests.map((interest) => {
            const checked = (currentInterests as string[]).includes(interest);
            const disabled = !checked && (currentInterests as string[]).length >= 4;
            return (
              <div
                key={interest}
                className={`flex items-center space-x-2 p-2 rounded border ${
                  checked ? "border-primary bg-primary/5" : "border-border"
                } ${disabled ? "opacity-50" : "cursor-pointer hover:bg-accent"}`}
                onClick={() => !disabled && toggleInterest(interest)}
              >
                <Checkbox checked={checked} disabled={disabled} />
                <span className="text-sm capitalize">{interest}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
FILE_EOF_16

echo "[17/18] Writing src/components/form/PreferencesSection.tsx..."
cat > frontend-react/src/components/form/PreferencesSection.tsx << 'FILE_EOF_17'
// src/components/form/PreferencesSection.tsx
import { useFormContext, Controller } from "react-hook-form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import type { AnalyzeRequest } from "@/types/request";

const RISK_OPTIONS = [
  { value: "low", label: "Low (capital preservation)" },
  { value: "medium", label: "Medium (balanced growth)" },
  { value: "high", label: "High (aggressive growth)" },
];

const HORIZON_OPTIONS = [
  { value: "1-3", label: "1-3 years (short term)" },
  { value: "3-5", label: "3-5 years (medium)" },
  { value: "5-8", label: "5-8 years (long)" },
  { value: "8+", label: "8+ years (very long)" },
];

export function PreferencesSection() {
  const { control } = useFormContext<AnalyzeRequest>();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label>Risk tolerance</Label>
        <Controller
          control={control}
          name="user.preferences.risk_profile"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {RISK_OPTIONS.map((r) => (
                  <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="space-y-2">
        <Label>Investment horizon</Label>
        <Controller
          control={control}
          name="user.preferences.horizon"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {HORIZON_OPTIONS.map((h) => (
                  <SelectItem key={h.value} value={h.value}>{h.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>
    </div>
  );
}
FILE_EOF_17

echo "[18/18] Writing src/components/form/StrategiesSection.tsx..."
cat > frontend-react/src/components/form/StrategiesSection.tsx << 'FILE_EOF_18'
// src/components/form/StrategiesSection.tsx
import { useFormContext } from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Buildings, House, ChartLine } from "@phosphor-icons/react";
import type { AnalyzeRequest } from "@/types/request";

const STRATEGIES = [
  {
    key: "business" as const,
    title: "Business",
    icon: Buildings,
    description: "Start or fund a side business (SaaS, e-commerce, services, passive income).",
    color: "text-blue-500",
  },
  {
    key: "real_estate" as const,
    title: "Real Estate",
    icon: House,
    description: "Direct property purchase with mortgage (rental, flip, commercial).",
    color: "text-green-500",
  },
  {
    key: "stock" as const,
    title: "Stocks / ETFs",
    icon: ChartLine,
    description: "Stock portfolio (ETFs, dividend, REITs, optional margin).",
    color: "text-purple-500",
  },
];

export function StrategiesSection() {
  const { register } = useFormContext<AnalyzeRequest>();

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-2">Configure each strategy</h2>
        <p className="text-sm text-muted-foreground">
          Specify how much to borrow and how much of your savings to use for each.
          Set loan amount to <code className="bg-muted px-1 rounded">0</code> to disable a strategy.
        </p>
      </div>

      {STRATEGIES.map(({ key, title, icon: Icon, description, color }) => (
        <Card key={key}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icon weight="duotone" className={`h-5 w-5 ${color}`} />
              {title}
            </CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <Label>Loan amount (USD)</Label>
                <Input
                  type="number"
                  min={0}
                  step={1000}
                  {...register(`config.${key}.loan_amount`, { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label>Loan years</Label>
                <Input
                  type="number"
                  min={0}
                  max={40}
                  {...register(`config.${key}.loan_years`, { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label>Savings to use</Label>
                <Input
                  type="number"
                  min={0}
                  step={1000}
                  {...register(`config.${key}.savings_to_use`, { valueAsNumber: true })}
                />
              </div>
              <div className="space-y-2">
                <Label>
                  Interest rate
                  <span className="text-xs text-muted-foreground ml-1">(decimal e.g. 0.055)</span>
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
      ))}
    </div>
  );
}
FILE_EOF_18

echo ""
echo "✅ All files installed!"
echo ""
echo "Next steps:"
echo "  1. cd frontend-react"
echo "  2. npx shadcn@latest add card input label select tabs badge separator form textarea checkbox slider skeleton sonner"
echo "  3. cd .. && make backend     # Terminal 1"
echo "  4. make frontend             # Terminal 2"
echo "  5. Open http://localhost:5173"