// src/components/form/FinancialSection.tsx
import { useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import type { AnalyzeRequest } from "@/types/request";

const FIELDS = [
  { key: "income" as const, label: "Monthly Income", short: "INCOME" },
  { key: "expenses" as const, label: "Monthly Expenses", short: "EXPENSES" },
  { key: "monthly_debt" as const, label: "Monthly Debt", short: "DEBT" },
  { key: "savings" as const, label: "Total Savings", short: "SAVINGS" },
];

export function FinancialSection() {
  const { register } = useFormContext<AnalyzeRequest>();

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {FIELDS.map(({ key, short }) => (
        <div key={key} className="space-y-2">
          <label
            htmlFor={key}
            className="block text-xs font-mono font-semibold uppercase tracking-wider text-muted-foreground"
          >
            {short}
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm font-mono">
              $
            </span>
            <Input
              id={key}
              type="number"
              min={0}
              step={100}
              className="h-11 pl-7 font-mono tabular-nums"
              {...register(`user.financial.${key}`, { valueAsNumber: true })}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
