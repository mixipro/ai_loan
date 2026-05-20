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
