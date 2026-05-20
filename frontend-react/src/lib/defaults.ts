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
