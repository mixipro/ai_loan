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
