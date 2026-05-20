// src/types/request.ts
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
  region: string;
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
  interests: string[];
  prior_experience: string;
  weekly_hours: WeeklyHours;

  // California-specific (optional)
  tech_role?: string;
  equity_compensation?: string;
  company_stage?: string;
  entertainment_role?: string;
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
