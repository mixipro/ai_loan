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
