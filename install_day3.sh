#!/bin/bash
# Day 3 — Warm palette + interactive loan calculator
set -e

if [ ! -d "frontend-react" ]; then
    echo "Run from project root: ~/PycharmProjects/ai_loan"
    exit 1
fi

echo "Day 3 — Warm palette + interactive loan calculator"
mkdir -p frontend-react/src/lib

echo "[1/4] Writing src/index.css..."
cat > frontend-react/src/index.css << 'FILE_EOF_01'
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";
@import "@fontsource-variable/geist";
@import "@fontsource-variable/geist-mono";

@custom-variant dark (&:is(.dark *));

@theme inline {
    --font-sans: 'Geist Variable', system-ui, -apple-system, sans-serif;
    --font-heading: 'Geist Variable', system-ui, sans-serif;
    --font-mono: 'Geist Mono Variable', monospace;

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

    /* Oble linije (more rounded) */
    --radius-sm: 0.5rem;
    --radius-md: 0.75rem;
    --radius-lg: 1rem;
    --radius-xl: 1.25rem;
}

:root {
    /* ─────────────────────────────────────────────
     * WARM PALETTE — cream + amber + sage (2026 style)
     * ───────────────────────────────────────────── */

    /* Background — warm cream (not cold white) */
    --background: oklch(0.985 0.008 85);
    --foreground: oklch(0.18 0.015 50);

    /* Cards */
    --card: oklch(0.99 0.005 85);
    --card-foreground: oklch(0.18 0.015 50);

    --popover: oklch(0.99 0.005 85);
    --popover-foreground: oklch(0.18 0.015 50);

    /* Primary — warm amber/terracotta */
    --primary: oklch(0.55 0.15 50);
    --primary-foreground: oklch(0.98 0.005 85);

    /* Secondary — warm cream */
    --secondary: oklch(0.93 0.03 100);
    --secondary-foreground: oklch(0.25 0.02 50);

    /* Muted — warm beige */
    --muted: oklch(0.94 0.02 85);
    --muted-foreground: oklch(0.50 0.02 60);

    /* Accent — sage green */
    --accent: oklch(0.92 0.04 130);
    --accent-foreground: oklch(0.25 0.05 130);

    /* Destructive — warm terra red */
    --destructive: oklch(0.55 0.20 25);
    --destructive-foreground: oklch(0.98 0.005 85);

    /* Borders */
    --border: oklch(0.88 0.02 85);
    --input: oklch(0.88 0.02 85);
    --ring: oklch(0.55 0.15 50);

    --radius: 0.875rem;

    /* Chart colors */
    --chart-1: oklch(0.62 0.18 45);
    --chart-2: oklch(0.60 0.10 150);
    --chart-3: oklch(0.55 0.15 25);
    --chart-4: oklch(0.65 0.12 90);
    --chart-5: oklch(0.50 0.10 280);

    /* Sidebar */
    --sidebar: oklch(0.97 0.01 85);
    --sidebar-foreground: oklch(0.18 0.015 50);
    --sidebar-primary: oklch(0.55 0.15 50);
    --sidebar-primary-foreground: oklch(0.98 0.005 85);
    --sidebar-accent: oklch(0.94 0.02 85);
    --sidebar-accent-foreground: oklch(0.25 0.02 50);
    --sidebar-border: oklch(0.88 0.02 85);
    --sidebar-ring: oklch(0.55 0.15 50);
}

@layer base {
    * { @apply border-border; }
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
    code, kbd, pre { font-family: var(--font-mono); }
    h1, h2, h3, h4 {
        font-family: var(--font-heading);
        letter-spacing: -0.02em;
        font-weight: 600;
    }
    .font-mono, .tabular-nums {
        font-family: var(--font-mono);
        font-feature-settings: "tnum";
    }
}

html { scroll-behavior: smooth; }

@keyframes fade-in {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in { animation: fade-in 0.4s ease-out; }

@keyframes slide-up {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-slide-up { animation: slide-up 0.5s ease-out; }

@keyframes gentle-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(184, 134, 75, 0.0); }
    50%      { box-shadow: 0 0 24px 4px rgba(184, 134, 75, 0.18); }
}
.animate-gentle-glow {
    animation: gentle-glow 3s ease-in-out infinite;
}
FILE_EOF_01

echo "[2/4] Writing src/lib/loanCalc.ts..."
cat > frontend-react/src/lib/loanCalc.ts << 'FILE_EOF_02'
// src/lib/loanCalc.ts
// Standard mortgage formula:
//   M = P × [r(1+r)^n] / [(1+r)^n - 1]
// where:
//   P = loan principal
//   r = monthly interest rate (annual / 12)
//   n = total number of payments (years × 12)

export interface LoanCalcResult {
  monthlyPayment: number;
  annualPayment: number;
  totalPaid: number;
  totalInterest: number;
}

export function calculateMonthlyPayment(
  principal: number,
  annualRate: number,
  years: number
): LoanCalcResult {
  // Validation
  if (principal <= 0 || years <= 0) {
    return { monthlyPayment: 0, annualPayment: 0, totalPaid: 0, totalInterest: 0 };
  }

  // Margin loan (0% interest, 0 years) — special case
  if (annualRate === 0 || years === 0) {
    return {
      monthlyPayment: 0,
      annualPayment: 0,
      totalPaid: principal,
      totalInterest: 0,
    };
  }

  const months = years * 12;
  const monthlyRate = annualRate / 12;

  const monthlyPayment =
    (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) /
    (Math.pow(1 + monthlyRate, months) - 1);

  const annualPayment = monthlyPayment * 12;
  const totalPaid = monthlyPayment * months;
  const totalInterest = totalPaid - principal;

  return {
    monthlyPayment: Math.round(monthlyPayment * 100) / 100,
    annualPayment: Math.round(annualPayment * 100) / 100,
    totalPaid: Math.round(totalPaid * 100) / 100,
    totalInterest: Math.round(totalInterest * 100) / 100,
  };
}

/**
 * Estimate max loan amount based on income, expenses, and DTI ratio.
 * Conservative California-style mortgage qualification.
 */
export function estimateMaxLoan(
  monthlyIncome: number,
  monthlyExpenses: number,
  monthlyDebt: number,
  annualRate: number,
  years: number,
  strategyType: "business" | "real_estate" | "stock"
): number {
  const availableForDebtService = monthlyIncome - monthlyExpenses - monthlyDebt;

  if (availableForDebtService <= 0) return 0;

  // DTI thresholds by strategy
  const maxDtiPct =
    strategyType === "real_estate" ? 0.45 : // mortgage stricter
    strategyType === "business" ? 0.35 :    // business loan moderate
    0.30;                                    // margin lenient

  const maxMonthlyPayment = monthlyIncome * maxDtiPct - monthlyDebt;

  if (maxMonthlyPayment <= 0) return 0;

  // Reverse mortgage formula to find principal
  if (annualRate === 0 || years === 0) {
    return maxMonthlyPayment * 12 * 5; // 5 years of payments roughly
  }

  const months = years * 12;
  const monthlyRate = annualRate / 12;
  const principal =
    (maxMonthlyPayment * (Math.pow(1 + monthlyRate, months) - 1)) /
    (monthlyRate * Math.pow(1 + monthlyRate, months));

  return Math.round(principal / 1000) * 1000;
}

export function formatUSD(value: number): string {
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export function formatUSDPrecise(value: number): string {
  return `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
FILE_EOF_02

echo "[3/4] Writing src/components/form/StrategiesSection.tsx..."
cat > frontend-react/src/components/form/StrategiesSection.tsx << 'FILE_EOF_03'
// src/components/form/StrategiesSection.tsx
import { useFormContext, useWatch } from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Buildings, House, ChartLine, Bank, Wallet, Calendar, Percent } from "@phosphor-icons/react";
import { calculateMonthlyPayment, formatUSD, formatUSDPrecise, estimateMaxLoan } from "@/lib/loanCalc";
import type { AnalyzeRequest } from "@/types/request";

interface StrategyMeta {
  key: "business" | "real_estate" | "stock";
  title: string;
  icon: typeof Buildings;
  description: string;
  color: string;
  bg: string;
  border: string;
  iconBg: string;
  loanMaxLimit: number;     // hard cap
  loanStep: number;
  yearsMax: number;
  rateMax: number;
}

const STRATEGIES: StrategyMeta[] = [
  {
    key: "business",
    title: "Business",
    icon: Buildings,
    description: "Start or fund a business (SaaS, e-commerce, services, passive income).",
    color: "text-blue-600",
    bg: "bg-blue-50/60",
    border: "border-blue-200",
    iconBg: "bg-blue-100",
    loanMaxLimit: 500000,
    loanStep: 5000,
    yearsMax: 10,
    rateMax: 0.20,
  },
  {
    key: "real_estate",
    title: "Real Estate",
    icon: House,
    description: "Direct property with mortgage (rental, flip, primary residence).",
    color: "text-emerald-600",
    bg: "bg-emerald-50/60",
    border: "border-emerald-200",
    iconBg: "bg-emerald-100",
    loanMaxLimit: 3000000,
    loanStep: 10000,
    yearsMax: 40,
    rateMax: 0.12,
  },
  {
    key: "stock",
    title: "Stocks / ETFs",
    icon: ChartLine,
    description: "Stock portfolio (ETFs, dividend, REITs, optional margin loan).",
    color: "text-amber-600",
    bg: "bg-amber-50/60",
    border: "border-amber-200",
    iconBg: "bg-amber-100",
    loanMaxLimit: 500000,
    loanStep: 5000,
    yearsMax: 10,
    rateMax: 0.15,
  },
];

// ──────────────────────────────────────────────────
// SLIDER + INPUT (synchronized)
// ──────────────────────────────────────────────────
interface SliderInputProps {
  label: string;
  icon: React.ReactNode;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
  formatter: (v: number) => string;
  hint?: string;
  maxLabel?: string;
}

function SliderInput({
  label, icon, value, onChange, min, max, step, formatter, hint, maxLabel,
}: SliderInputProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium flex items-center gap-1.5">
          {icon}
          {label}
        </Label>
        <div className="flex items-center gap-1">
          <span className="text-sm font-mono font-semibold text-primary tabular-nums">
            {formatter(value)}
          </span>
          {maxLabel && (
            <span className="text-xs text-muted-foreground tabular-nums">/ {maxLabel}</span>
          )}
        </div>
      </div>

      <Slider
        value={[value]}
        onValueChange={([v]) => onChange(v)}
        min={min}
        max={max}
        step={step}
        className="my-2"
      />

      <div className="flex items-center justify-between gap-2">
        <Input
          type="number"
          value={value}
          onChange={(e) => {
            const v = Number(e.target.value);
            if (!isNaN(v)) onChange(Math.max(min, Math.min(max, v)));
          }}
          min={min}
          max={max}
          step={step}
          className="h-8 text-sm font-mono w-32"
        />
        {hint && (
          <span className="text-xs text-muted-foreground italic">{hint}</span>
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────
// STRATEGY CARD with live calculator
// ──────────────────────────────────────────────────
interface StrategyCardProps {
  meta: StrategyMeta;
  maxLoanFromBackend: number;
  monthlyIncome: number;
  monthlyExpenses: number;
  monthlyDebt: number;
  totalSavings: number;
}

function StrategyCard({
  meta, maxLoanFromBackend, monthlyIncome, monthlyExpenses, monthlyDebt, totalSavings,
}: StrategyCardProps) {
  const { control, setValue } = useFormContext<AnalyzeRequest>();
  const cfg = useWatch({ control, name: `config.${meta.key}` });

  const loanAmount = cfg?.loan_amount ?? 0;
  const loanYears = cfg?.loan_years ?? 0;
  const savingsToUse = cfg?.savings_to_use ?? 0;
  const interestRate = cfg?.interest_rate ?? 0;

  // ─── Live calculations ───
  const loan = calculateMonthlyPayment(loanAmount, interestRate, loanYears);
  const totalCapital = loanAmount + savingsToUse;
  const isDisabled = loanAmount === 0 && savingsToUse === 0;

  // Estimate max loan client-side
  const estimatedMax = estimateMaxLoan(
    monthlyIncome,
    monthlyExpenses,
    monthlyDebt,
    interestRate || 0.055,
    loanYears || 10,
    meta.key
  );

  // Use backend max if available, else estimated, else hard limit
  const effectiveMaxLoan = Math.min(
    maxLoanFromBackend || estimatedMax || meta.loanMaxLimit,
    meta.loanMaxLimit
  );

  const Icon = meta.icon;

  // ─── Handlers ───
  const setLoan = (v: number) => setValue(`config.${meta.key}.loan_amount`, v);
  const setYears = (v: number) => setValue(`config.${meta.key}.loan_years`, v);
  const setSavings = (v: number) => setValue(`config.${meta.key}.savings_to_use`, v);
  const setRate = (v: number) => setValue(`config.${meta.key}.interest_rate`, v);

  // ─── Visual: Capital allocation bar ───
  const loanPct = totalCapital > 0 ? (loanAmount / totalCapital) * 100 : 0;
  const savingsPct = totalCapital > 0 ? (savingsToUse / totalCapital) * 100 : 0;

  return (
    <Card className={`overflow-hidden transition-all ${isDisabled ? "opacity-60" : "hover:shadow-md"}`}>
      {/* HEADER */}
      <CardHeader className={`${meta.bg} ${meta.border} border-b pb-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${meta.iconBg} shadow-sm`}>
              <Icon weight="duotone" className={`h-6 w-6 ${meta.color}`} />
            </div>
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                {meta.title}
                {isDisabled && <Badge variant="secondary" className="text-xs">Disabled</Badge>}
              </CardTitle>
              <CardDescription className="text-xs">{meta.description}</CardDescription>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Total Capital</div>
            <div className="text-lg font-bold tabular-nums">{formatUSD(totalCapital)}</div>
          </div>
        </div>

        {/* Capital allocation visual bar */}
        {totalCapital > 0 && (
          <div className="mt-3">
            <div className="flex h-2 rounded-full overflow-hidden bg-background">
              {loanAmount > 0 && (
                <div
                  className="bg-foreground/60 transition-all"
                  style={{ width: `${loanPct}%` }}
                  title={`Loan: ${formatUSD(loanAmount)}`}
                />
              )}
              {savingsToUse > 0 && (
                <div
                  className={`${meta.color.replace("text-", "bg-")} opacity-80 transition-all`}
                  style={{ width: `${savingsPct}%` }}
                  title={`Savings: ${formatUSD(savingsToUse)}`}
                />
              )}
            </div>
            <div className="flex items-center justify-between mt-1.5 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 rounded-full bg-foreground/60" />
                Loan: <span className="font-mono tabular-nums">{formatUSD(loanAmount)} ({loanPct.toFixed(0)}%)</span>
              </span>
              <span className="flex items-center gap-1">
                <span className={`inline-block w-2 h-2 rounded-full ${meta.color.replace("text-", "bg-")} opacity-80`} />
                Savings: <span className="font-mono tabular-nums">{formatUSD(savingsToUse)} ({savingsPct.toFixed(0)}%)</span>
              </span>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-5 space-y-5">
        {/* LOAN AMOUNT */}
        <SliderInput
          label="Loan Amount"
          icon={<Bank weight="duotone" className="h-4 w-4 text-muted-foreground" />}
          value={loanAmount}
          onChange={setLoan}
          min={0}
          max={effectiveMaxLoan}
          step={meta.loanStep}
          formatter={formatUSD}
          maxLabel={formatUSD(effectiveMaxLoan)}
          hint={maxLoanFromBackend > 0 ? `Max approved` : `Estimated max`}
        />

        {/* SAVINGS TO USE */}
        <SliderInput
          label="Savings to Use"
          icon={<Wallet weight="duotone" className="h-4 w-4 text-muted-foreground" />}
          value={savingsToUse}
          onChange={setSavings}
          min={0}
          max={totalSavings}
          step={meta.loanStep / 5}
          formatter={formatUSD}
          maxLabel={formatUSD(totalSavings)}
          hint={`Of ${formatUSD(totalSavings)} total`}
        />

        {/* LOAN YEARS */}
        {loanAmount > 0 && (
          <SliderInput
            label="Loan Term"
            icon={<Calendar weight="duotone" className="h-4 w-4 text-muted-foreground" />}
            value={loanYears}
            onChange={setYears}
            min={meta.key === "stock" ? 0 : 1}
            max={meta.yearsMax}
            step={1}
            formatter={(v) => v === 0 ? "On-demand" : `${v} year${v !== 1 ? "s" : ""}`}
          />
        )}

        {/* INTEREST RATE */}
        {loanAmount > 0 && (
          <SliderInput
            label="Interest Rate"
            icon={<Percent weight="duotone" className="h-4 w-4 text-muted-foreground" />}
            value={interestRate}
            onChange={setRate}
            min={0}
            max={meta.rateMax}
            step={0.001}
            formatter={(v) => `${(v * 100).toFixed(2)}%`}
            hint="Decimal: 0.055 = 5.5%"
          />
        )}

        {/* LIVE MONTHLY PAYMENT */}
        {loanAmount > 0 && loanYears > 0 && interestRate > 0 && (
          <div className={`${meta.bg} ${meta.border} border rounded-xl p-4 space-y-2 animate-fade-in`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Monthly Payment
              </span>
              <Badge variant="outline" className="text-xs">Estimated</Badge>
            </div>
            <div className="flex items-baseline gap-2">
              <span className={`text-2xl font-bold tabular-nums ${meta.color}`}>
                {formatUSDPrecise(loan.monthlyPayment)}
              </span>
              <span className="text-xs text-muted-foreground">/month</span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-2 border-t text-xs">
              <div>
                <div className="text-muted-foreground">Annual</div>
                <div className="font-mono tabular-nums font-medium">{formatUSD(loan.annualPayment)}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Total paid</div>
                <div className="font-mono tabular-nums font-medium">{formatUSD(loan.totalPaid)}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Total interest</div>
                <div className="font-mono tabular-nums font-medium text-destructive">{formatUSD(loan.totalInterest)}</div>
              </div>
            </div>
          </div>
        )}

        {/* MARGIN LOAN INFO (special case for stocks) */}
        {meta.key === "stock" && loanAmount > 0 && loanYears === 0 && (
          <div className={`${meta.bg} ${meta.border} border rounded-xl p-3 text-xs animate-fade-in`}>
            <strong>Margin loan:</strong> Interest-only, no fixed term. Pay interest monthly. Repay principal anytime (or be forced to repay if portfolio drops 25%+).
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ──────────────────────────────────────────────────
// MAIN COMPONENT
// ──────────────────────────────────────────────────
export function StrategiesSection() {
  const { control } = useFormContext<AnalyzeRequest>();
  const financial = useWatch({ control, name: "user.financial" });

  // From form
  const monthlyIncome = financial?.income ?? 0;
  const monthlyExpenses = financial?.expenses ?? 0;
  const monthlyDebt = financial?.monthly_debt ?? 0;
  const totalSavings = financial?.savings ?? 0;

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold mb-1">Configure each strategy</h2>
        <p className="text-sm text-muted-foreground">
          Use the sliders to set how much to borrow and how much of your savings to invest.
          See your monthly payment update in real time.
        </p>
      </div>

      {STRATEGIES.map((meta) => (
        <StrategyCard
          key={meta.key}
          meta={meta}
          maxLoanFromBackend={0}  /* TODO: pass from backend after first call */
          monthlyIncome={monthlyIncome}
          monthlyExpenses={monthlyExpenses}
          monthlyDebt={monthlyDebt}
          totalSavings={totalSavings}
        />
      ))}
    </div>
  );
}
FILE_EOF_03

echo "[4/4] Writing src/pages/FormPage.tsx..."
cat > frontend-react/src/pages/FormPage.tsx << 'FILE_EOF_04'
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
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import type { AnalyzeRequest } from "@/types/request";
import { PersonalSection } from "@/components/form/PersonalSection";
import { LocationSection } from "@/components/form/LocationSection";
import { FinancialSection } from "@/components/form/FinancialSection";
import { ProfessionalSection } from "@/components/form/ProfessionalSection";
import { PreferencesSection } from "@/components/form/PreferencesSection";
import { StrategiesSection } from "@/components/form/StrategiesSection";
import {
  MapPin, Briefcase, CurrencyDollar, ChartLine, Sparkle,
  User, Gear, CaretRight, FlaskOff
} from "@phosphor-icons/react";

export function FormPage() {
  const navigate = useNavigate();
  const optionsQuery = useOptions();
  const analyzeMutation = useAnalyze();
  const [activeTab, setActiveTab] = useState("profile");

  const methods = useForm<AnalyzeRequest>({
    defaultValues: DEMO_PROFILES.truck_driver.data,
    mode: "onChange",
  });

  const loadDemo = (key: string) => {
    if (key in DEMO_PROFILES) {
      methods.reset(DEMO_PROFILES[key as DemoProfileKey].data);
    }
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

  if (optionsQuery.isLoading) {
    return (
      <div className="container mx-auto py-8 max-w-5xl px-4 space-y-4">
        <Skeleton className="h-12 w-1/3" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (optionsQuery.isError) {
    return (
      <div className="container mx-auto py-8 max-w-3xl px-4">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Cannot reach backend</CardTitle>
            <CardDescription>
              Make sure FastAPI is running:{" "}
              <code className="bg-muted px-2 py-0.5 rounded text-xs">make backend</code>
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const options = optionsQuery.data!;

  return (
    <div className="container mx-auto py-6 max-w-5xl px-4 animate-fade-in">
      {/* HEADER — demo profiles tucked into dropdown */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
            <Sparkle weight="duotone" className="text-primary h-9 w-9" />
            CaliforniaCFO
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            AI-powered investment advisor for California residents
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Demo profile dropdown — compact replacement for big QuickStart block */}
          <Select onValueChange={loadDemo}>
            <SelectTrigger className="h-9 w-[210px] text-xs">
              <FlaskOff weight="duotone" className="h-3.5 w-3.5 mr-1" />
              <SelectValue placeholder="Load demo profile…" />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(DEMO_PROFILES) as DemoProfileKey[]).map((key) => (
                <SelectItem key={key} value={key} className="text-xs">
                  {DEMO_PROFILES[key].label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Badge variant="outline" className="text-xs">v5.2.5</Badge>
        </div>
      </div>

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
                  <CaretRight weight="bold" className="h-4 w-4" />
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
                  className="min-w-[240px] gap-2"
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
FILE_EOF_04

echo ""
echo "✅ Day 3 installed!"
echo ""
echo "Next:"
echo "  1. Restart Vite (Ctrl+C in frontend terminal, then make frontend)"
echo "  2. Hard refresh browser (Ctrl+Shift+R)"
echo "  3. Click Strategies tab and play with sliders"
