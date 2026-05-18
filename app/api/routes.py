# app/api/routes.py
"""
API routes for CaliforniaCFO.

Endpoints:
  POST /analyze       — Main analysis (3 agents with user config)
  POST /loan-offers   — Max loan amounts per loan type (defined separately)
  GET  /options       — Catalog values for frontend dropdowns
  GET  /info          — System metadata
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.user import (
    UserInput, Currency,
    CaliforniaSector,
    EmploymentStatus, RiskProfile, HorizonGroup, WeeklyHours,
    CITIES_BY_REGION, PREDEFINED_INTERESTS,
    TechRole, EquityCompensation, CompanyStage, EntertainmentRole,
)
from app.core.california_config import REGION_DATA
from app.core.profession_catalog import PROFESSIONS_BY_SECTOR, get_all_professions
from app.services.orchestrator import run_pipeline

router = APIRouter()


# ─────────────────────────
# 📋 PYDANTIC MODELS — Per-strategy config
# ─────────────────────────
class StrategyConfig(BaseModel):
    """User-configurable capital allocation for one strategy."""
    loan_amount: float = Field(default=0, ge=0)
    loan_years: int = Field(default=0, ge=0, le=30)
    savings_to_use: float = Field(default=0, ge=0)
    interest_rate: float = Field(default=0, ge=0, le=1)


class AnalyzeConfig(BaseModel):
    """Per-strategy configuration sent by the frontend after /loan-offers."""
    business: StrategyConfig = Field(default_factory=StrategyConfig)
    real_estate: StrategyConfig = Field(default_factory=StrategyConfig)
    stock: StrategyConfig = Field(default_factory=StrategyConfig)


class AnalyzeRequest(BaseModel):
    """Full /analyze request body."""
    user: UserInput
    config: AnalyzeConfig


# ─────────────────────────
# 🎯 ENDPOINTS
# ─────────────────────────
@router.post("/analyze")
async def analyze_user(payload: AnalyzeRequest):
    """
    Main analysis endpoint — runs 3 strategy agents with user-specified config.

    Expected flow:
      1. Frontend calls /loan-offers first → gets max amounts per loan type
      2. User adjusts sliders for each strategy
      3. Frontend calls /analyze with the user's selected config

    Each strategy uses its OWN loan_amount + savings_to_use from config.
    Real estate enforces 20% min down payment.
    Stock margin enforces 50% max LTV.
    """
    try:
        return await run_pipeline(payload.user, payload.config.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/options")
async def get_options():
    """
    Returns California-specific enum values and constants for frontend dropdowns.

    Key field: `professions_by_sector` — 436 California-focused professions
    organized by 12 sectors, used by the frontend to cascade
    sector → profession dropdown.
    """
    return {
        # ─── Location ───
        "regions": [
            {
                "value": region.value,
                "label": data["display_name"],
                "description": data["description"],
                "primary_industries": data["primary_industries"],
            }
            for region, data in REGION_DATA.items()
        ],
        "cities_by_region": CITIES_BY_REGION,

        # ─── Currency ───
        "currencies": [c.value for c in Currency],

        # ─── Professional ───
        "sectors": [s.value for s in CaliforniaSector],

        # ⭐ Sector → Profession mapping (436 professions)
        "professions_by_sector": PROFESSIONS_BY_SECTOR,

        # Flat list of all professions (for autocomplete / search)
        "all_professions": get_all_professions(),

        "employment_statuses": [e.value for e in EmploymentStatus],

        # ─── California-specific (Tech / Entertainment) ───
        "tech_roles": [t.value for t in TechRole],
        "equity_compensations": [e.value for e in EquityCompensation],
        "company_stages": [c.value for c in CompanyStage],
        "entertainment_roles": [e.value for e in EntertainmentRole],

        # ─── Preferences ───
        "risk_profiles": [r.value for r in RiskProfile],
        "horizons": [h.value for h in HorizonGroup],
        "weekly_hours": [w.value for w in WeeklyHours],
        "predefined_interests": PREDEFINED_INTERESTS,
    }


@router.get("/info")
async def get_system_info():
    """System metadata for frontend branding and defense narrative."""
    return {
        "name": "CaliforniaCFO",
        "tagline": "AI Financial Advisor That Actually Knows California",
        "version": "4.1.0",
        "specialization": "California, USA",
        "regions_covered": len(REGION_DATA),
        "cities_covered": sum(len(data["cities"]) for data in REGION_DATA.values()),
        "professions_covered": sum(len(p) for p in PROFESSIONS_BY_SECTOR.values()),
        "sectors_covered": len(PROFESSIONS_BY_SECTOR),
        "architecture": "3-agent config-driven (business + real_estate + stock)",
        "features": [
            "User-configurable capital allocation per strategy",
            "Cash / Loan / Mixed funding modes (per strategy)",
            "California-specific tax calculations (Prop 13, QSBS, state tax)",
            "Region-aware risk scoring (8 California regions)",
            "Cost-of-living adjusted financial planning",
            "RAG-based California expert knowledge (51 chunks)",
            "436+ California-focused professions across 12 sectors",
            "Strict mortgage requirements (20% min down payment)",
            "Margin LTV cap (50% max)",
        ],
        "supported_industries": [s.value for s in CaliforniaSector],
    }