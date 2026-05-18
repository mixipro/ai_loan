# app/models/user.py
"""
User input models for CaliforniaCFO.

v4.1 Changes:
  - Profession is now plain `str` (not Enum) — supports 436 California-focused
    professions from app.core.profession_catalog without enum limitations
  - CaliforniaSector aligned with frontend values (no " & Media" suffix etc.)
  - City validator softened (warning instead of error if not in catalog)
  - Removed unused Profession enum (replaced by profession_catalog)
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from enum import Enum
from app.core.california_config import (
    CaliforniaRegion, REGION_DATA,
    get_cities_for_region, find_region_for_city
)


# ─────────────────────────────────────────
# 🌴 CALIFORNIA LOCATION
# ─────────────────────────────────────────

CITIES_BY_REGION: dict[str, list[str]] = {
    region.value: data["cities"]
    for region, data in REGION_DATA.items()
}


class LocationInfo(BaseModel):
    """Region + city. City must be non-empty string (validated against catalog softly)."""
    region: CaliforniaRegion
    city: str = Field(..., min_length=1, description="City name within the selected region")

    @model_validator(mode="after")
    def city_should_be_in_region(self) -> "LocationInfo":
        """
        Soft validation: if city is in CITIES_BY_REGION catalog, ensure it matches the region.
        If city is custom (not in catalog), accept it (user knows their own city).
        """
        valid_cities = get_cities_for_region(self.region)
        all_cities = set()
        for cities in CITIES_BY_REGION.values():
            all_cities.update(cities)

        # If city is in catalog but in WRONG region → reject (mismatch)
        if self.city in all_cities and self.city not in valid_cities:
            actual_region = find_region_for_city(self.city)
            raise ValueError(
                f"'{self.city}' belongs to {actual_region.value if actual_region else 'unknown region'}, "
                f"not {self.region.value}. Pick a city from: {valid_cities[:5]}..."
            )
        # If city is unknown (custom) → accept silently
        return self


# ─────────────────────────────────────────
# 💰 FINANCIAL
# ─────────────────────────────────────────

class Currency(str, Enum):
    USD = "USD"


class FinancialInfo(BaseModel):
    income: int = Field(..., gt=0, description="Monthly income (USD)")
    expenses: int = Field(..., ge=0, description="Monthly expenses (USD)")
    monthly_debt: int = Field(..., ge=0, description="Monthly debt payment (USD)")
    savings: int = Field(..., ge=0, le=10_000_000, description="Total savings (USD, max $10M)")
    currency: Currency = Field(default=Currency.USD)

    @model_validator(mode="after")
    def expenses_lt_income(self) -> "FinancialInfo":
        if self.expenses >= self.income:
            raise ValueError("Expenses cannot exceed or equal income.")
        return self


# ─────────────────────────────────────────
# 💼 PROFESSIONAL — CALIFORNIA SECTORS
# Aligned with frontend dropdown values (12 sectors)
# ─────────────────────────────────────────

class CaliforniaSector(str, Enum):
    """California-specific industry sectors. Values match frontend dropdown."""
    TECHNOLOGY = "Technology"
    ENTERTAINMENT = "Entertainment"
    BIOTECHNOLOGY = "Biotechnology"
    HEALTHCARE = "Healthcare"
    AGRICULTURE = "Agriculture"
    GOVERNMENT = "Government"
    FINANCE = "Finance"
    EDUCATION = "Education"
    TOURISM = "Tourism"
    MANUFACTURING = "Manufacturing"
    RETAIL = "Retail"
    OTHER = "Other"


# NOTE: Profession is now plain `str`, not Enum.
# 436 California-focused professions are catalogued in app/core/profession_catalog.py
# and exposed via /options endpoint for the frontend dropdown.


class EmploymentStatus(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    FREELANCER = "freelancer"
    SELF_EMPLOYED = "self-employed"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    RETIRED = "retired"


class RiskProfile(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def goal(self) -> str:
        return {
            RiskProfile.LOW: "safety",
            RiskProfile.MEDIUM: "growth",
            RiskProfile.HIGH: "profit",
        }[self]


# ─────────────────────────────────────────
# 🌴 CALIFORNIA-SPECIFIC PROFESSIONAL FIELDS (optional)
# Used for Tech / Entertainment sectors
# ─────────────────────────────────────────

class TechRole(str, Enum):
    SOFTWARE_ENGINEER = "Software Engineer"
    PRODUCT_MANAGER = "Product Manager"
    DESIGNER = "Designer (UX/UI)"
    DATA_SCIENTIST = "Data Scientist"
    DEVOPS_SRE = "DevOps / SRE"
    SECURITY = "Security Engineer"
    HARDWARE = "Hardware Engineer"
    QA = "QA / Test Engineer"
    ENGINEERING_MANAGER = "Engineering Manager"
    EXECUTIVE = "Tech Executive (VP/CTO/CEO)"
    OTHER_TECH = "Other Tech Role"


class EquityCompensation(str, Enum):
    NONE = "None"
    ISO = "ISO (Incentive Stock Options)"
    NSO = "NSO (Non-qualified Stock Options)"
    RSU = "RSU (Restricted Stock Units)"
    ESPP = "ESPP (Employee Stock Purchase)"
    FOUNDER_STOCK = "Founder Stock"
    MIXED = "Mixed (RSUs + Options)"


class CompanyStage(str, Enum):
    PRE_SEED = "Pre-seed Startup"
    SEED = "Seed Stage Startup"
    SERIES_A_B = "Series A-B"
    SERIES_C_PLUS = "Series C+"
    PRE_IPO = "Pre-IPO / Late Stage"
    PUBLIC = "Public Company"
    FAANG = "Big Tech / FAANG"
    GOVERNMENT = "Government"
    NONPROFIT = "Nonprofit"
    SMALL_BUSINESS = "Small Business"
    NA = "Not Applicable"


class EntertainmentRole(str, Enum):
    ABOVE_LINE = "Above-the-line (Writer/Director/Producer)"
    BELOW_LINE = "Below-the-line (Crew)"
    PERFORMER = "Performer (Actor/Musician)"
    EXECUTIVE = "Studio Executive"
    INDEPENDENT_CONTRACTOR = "Independent Contractor"
    AGENT_MANAGER = "Agent / Manager"
    NA = "Not Applicable"


# ─────────────────────────────────────────
# ⏰ WEEKLY HOURS & HORIZON
# ─────────────────────────────────────────

class WeeklyHours(str, Enum):
    MINIMAL = "0-5"
    LIGHT = "5-15"
    MODERATE = "15-30"
    HEAVY = "30+"


class HorizonGroup(str, Enum):
    SHORT = "1-3"
    MEDIUM = "3-5"
    LONG = "5-8"
    VERY_LONG = "8+"


class Preferences(BaseModel):
    risk_profile: RiskProfile
    horizon: HorizonGroup


# ─────────────────────────────────────────
# 🎯 PREDEFINED INTERESTS (50 options)
# ─────────────────────────────────────────

PREDEFINED_INTERESTS = [
    # Sport & fitness
    "fitness", "yoga", "running", "cycling", "swimming",
    "team sports", "martial arts", "hiking", "rock climbing", "skiing",

    # Food & drink
    "cooking", "baking", "wine", "coffee", "barbecue",

    # Tech & gaming
    "programming", "ai/ml", "gaming", "blockchain", "robotics",
    "technology", "startups",

    # Creative
    "photography", "videography", "music", "writing", "drawing",
    "design", "fashion", "interior design", "crafts", "art",

    # Business & finance
    "investing", "real estate", "crypto", "trading",

    # Travel & lifestyle
    "travel", "languages", "history", "cultures", "outdoor adventure",

    # Wellness & lifestyle
    "meditation", "psychology", "self-improvement", "minimalism", "sustainability",

    # Education & hobbies
    "reading", "podcasts", "online courses", "board games", "puzzles",
    "gardening",
]


# ─────────────────────────────────────────
# 💼 PROFESSIONAL INFO
# ─────────────────────────────────────────

class ProfessionalInfo(BaseModel):
    """
    Professional profile. Sector is enum (12 values), profession is plain string
    (validated only as non-empty — frontend ensures it comes from PROFESSIONS_BY_SECTOR).
    """
    sector: CaliforniaSector
    profession: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Profession name (selected from sector-filtered catalog of 436 California professions)"
    )
    employment_status: EmploymentStatus

    interests: List[str] = Field(
        default_factory=list,
        description="User's hobbies and interests (max 4)",
        max_length=4
    )
    prior_experience: str = Field(
        default="",
        max_length=500,
        description="Brief description of previous businesses/projects"
    )
    weekly_hours: WeeklyHours = Field(
        default=WeeklyHours.LIGHT,
        description="Hours per week available for business/investment activity"
    )

    # California-specific optional fields
    tech_role: Optional[TechRole] = Field(
        default=None,
        description="Specific tech role (Bay Area / Silicon Valley focus)"
    )
    equity_compensation: Optional[EquityCompensation] = Field(
        default=None,
        description="Type of equity compensation received (RSU, ISO, Founder, etc.)"
    )
    company_stage: Optional[CompanyStage] = Field(
        default=None,
        description="Stage of current employer (especially for tech/biotech sectors)"
    )
    qsbs_eligible: Optional[bool] = Field(
        default=None,
        description="Stock qualifies for QSBS exclusion under Section 1202?"
    )
    entertainment_role: Optional[EntertainmentRole] = Field(
        default=None,
        description="Entertainment industry role (LA / Hollywood focus)"
    )


# ─────────────────────────────────────────
# 👤 PERSONAL INFO
# ─────────────────────────────────────────

class PersonalInfo(BaseModel):
    age: int = Field(..., gt=17, lt=120, description="Age (18-119)")


# ─────────────────────────────────────────
# 🔥 FINAL USER INPUT
# ─────────────────────────────────────────

class UserInput(BaseModel):
    """Complete user profile submitted to /loan-offers and /analyze endpoints."""
    personal: PersonalInfo
    location: LocationInfo
    financial: FinancialInfo
    professional: ProfessionalInfo
    preferences: Preferences