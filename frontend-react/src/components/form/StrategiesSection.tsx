// src/components/form/StrategiesSection.tsx
import { useEffect } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
  loanMaxLimit: number;
  loanStep: number;     // dollar-level granularity
  yearsMax: number;
  yearsMin: number;
  rateMax: number;
  defaultRate: number;
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
    loanStep: 100,        // ← changed from 5000 to 100
    yearsMax: 10,
    yearsMin: 1,
    rateMax: 0.20,
    defaultRate: 0.07,
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
    loanStep: 100,        // ← changed from 10000 to 100
    yearsMax: 30,         // ← FIXED: backend constraint is ≤30
    yearsMin: 5,
    rateMax: 0.12,
    defaultRate: 0.055,
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
    loanStep: 100,        // ← changed from 5000 to 100
    yearsMax: 10,
    yearsMin: 0,          // margin can be 0
    rateMax: 0.15,
    defaultRate: 0.085,
  },
];

// ──────────────────────────────────────────────────
// SLIDER + INPUT (synchronized, finer granularity)
// ──────────────────────────────────────────────────
interface SliderInputProps {
  label: string;
  icon: React.ReactNode;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;          // for slider
  inputStep?: number;    // for input (default = 1 for dollars)
  formatter: (v: number) => string;
  hint?: string;
  maxLabel?: string;
  isWarning?: boolean;
}

function SliderInput({
  label, icon, value, onChange, min, max, step, inputStep = 1, formatter, hint, maxLabel, isWarning,
}: SliderInputProps) {
  // Clamp value to slider range
  const sliderValue = Math.min(Math.max(value, min), max);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium flex items-center gap-1.5">
          {icon}
          {label}
        </label>
        <div className="flex items-center gap-1">
          <span className={`text-sm font-mono font-semibold tabular-nums ${
            isWarning ? "text-destructive" : "text-primary"
          }`}>
            {formatter(value)}
          </span>
          {maxLabel && (
            <span className="text-xs text-muted-foreground tabular-nums">/ {maxLabel}</span>
          )}
        </div>
      </div>

      <Slider
        value={[sliderValue]}
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
            const raw = e.target.value;
            if (raw === "") {
              onChange(0);
              return;
            }
            const v = Number(raw);
            if (!isNaN(v)) {
              // Allow ANY dollar amount in input (overrides slider step)
              onChange(Math.max(min, Math.min(max, v)));
            }
          }}
          min={min}
          max={max}
          step={inputStep}
          className="h-8 text-sm font-mono w-32"
        />
        {hint && (
          <span className={`text-xs italic ${isWarning ? "text-destructive" : "text-muted-foreground"}`}>
            {hint}
          </span>
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
  monthlyIncome: number;
  monthlyExpenses: number;
  monthlyDebt: number;
  totalSavings: number;
}

function StrategyCard({
  meta, monthlyIncome, monthlyExpenses, monthlyDebt, totalSavings,
}: StrategyCardProps) {
  const { control, setValue } = useFormContext<AnalyzeRequest>();
  const cfg = useWatch({ control, name: `config.${meta.key}` });

  const loanAmount = cfg?.loan_amount ?? 0;
  const loanYears = cfg?.loan_years ?? 0;
  const savingsToUse = cfg?.savings_to_use ?? 0;
  const interestRate = cfg?.interest_rate ?? 0;

  // ─── Estimated max (client-side approximation) ───
  const estimatedMax = estimateMaxLoan(
    monthlyIncome,
    monthlyExpenses,
    monthlyDebt,
    interestRate || meta.defaultRate,
    loanYears || (meta.yearsMin > 0 ? meta.yearsMin : 5),
    meta.key
  );

  // Use estimated max as slider ceiling, but allow input override
  const sliderMaxLoan = Math.max(estimatedMax, meta.loanMaxLimit / 6);  // sane floor
  const effectiveMaxLoan = Math.min(sliderMaxLoan, meta.loanMaxLimit);

  // ─── AUTO-CAP DEFAULT LOAN AT ESTIMATED MAX (one-time on mount) ───
  // This fixes "Loan $80k > estimated max $75k" issue
  useEffect(() => {
    if (loanAmount > effectiveMaxLoan && estimatedMax > 0) {
      setValue(`config.${meta.key}.loan_amount`, effectiveMaxLoan);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);  // mount only

  // ─── Enforce real_estate yearsMax = 30 (backend constraint) ───
  useEffect(() => {
    if (meta.key === "real_estate" && loanYears > meta.yearsMax) {
      setValue(`config.real_estate.loan_years`, meta.yearsMax);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loanYears]);

  // ─── Live calculations ───
  const loan = calculateMonthlyPayment(loanAmount, interestRate, loanYears);
  const totalCapital = loanAmount + savingsToUse;
  const isDisabled = loanAmount === 0 && savingsToUse === 0;

  // ─── Warning state ───
  const loanExceedsMax = loanAmount > effectiveMaxLoan;

  const Icon = meta.icon;

  // ─── Setters ───
  const setLoan = (v: number) => setValue(`config.${meta.key}.loan_amount`, v);
  const setYears = (v: number) => setValue(`config.${meta.key}.loan_years`, v);
  const setSavings = (v: number) => setValue(`config.${meta.key}.savings_to_use`, v);
  const setRate = (v: number) => setValue(`config.${meta.key}.interest_rate`, v);

  // ─── Capital bar ───
  const loanPct = totalCapital > 0 ? (loanAmount / totalCapital) * 100 : 0;
  const savingsPct = totalCapital > 0 ? (savingsToUse / totalCapital) * 100 : 0;

  return (
    <Card className={`overflow-hidden transition-all ${isDisabled ? "opacity-60" : "hover:shadow-md"}`}>
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
          inputStep={1}
          formatter={formatUSD}
          maxLabel={formatUSD(effectiveMaxLoan)}
          hint={loanExceedsMax ? "⚠️ Exceeds estimated max" : "Estimated max"}
          isWarning={loanExceedsMax}
        />

        {/* SAVINGS TO USE */}
        <SliderInput
          label="Savings to Use"
          icon={<Wallet weight="duotone" className="h-4 w-4 text-muted-foreground" />}
          value={savingsToUse}
          onChange={setSavings}
          min={0}
          max={totalSavings}
          step={meta.loanStep}
          inputStep={1}
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
            min={meta.yearsMin}
            max={meta.yearsMax}
            step={1}
            inputStep={1}
            formatter={(v) => v === 0 ? "On-demand (margin)" : `${v} year${v !== 1 ? "s" : ""}`}
            hint={meta.key === "real_estate" ? "Max 30 years (mortgage)" : undefined}
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
            inputStep={0.001}
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

        {/* MARGIN LOAN INFO */}
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
// MAIN
// ──────────────────────────────────────────────────
export function StrategiesSection() {
  const { control } = useFormContext<AnalyzeRequest>();
  const financial = useWatch({ control, name: "user.financial" });

  const monthlyIncome = financial?.income ?? 0;
  const monthlyExpenses = financial?.expenses ?? 0;
  const monthlyDebt = financial?.monthly_debt ?? 0;
  const totalSavings = financial?.savings ?? 0;

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold mb-1">Configure each strategy</h2>
        <p className="text-sm text-muted-foreground">
          Use the sliders to set loan amount and savings to invest. Type exact dollar amounts in the input fields.
          See your monthly payment update in real time.
        </p>
      </div>

      {STRATEGIES.map((meta) => (
        <StrategyCard
          key={meta.key}
          meta={meta}
          monthlyIncome={monthlyIncome}
          monthlyExpenses={monthlyExpenses}
          monthlyDebt={monthlyDebt}
          totalSavings={totalSavings}
        />
      ))}
    </div>
  );
}
