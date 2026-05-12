# app/api/routes.py

from fastapi import APIRouter, HTTPException
from app.models.user import (
    UserInput, Currency,
    CaliforniaSector, Profession,
    EmploymentStatus, RiskProfile, HorizonGroup, WeeklyHours,
    CITIES_BY_REGION, PREDEFINED_INTERESTS,
    # California-specific
    TechRole, EquityCompensation, CompanyStage, EntertainmentRole,
)
from app.core.california_config import (
    CaliforniaRegion, REGION_DATA,
)
from app.models.simulation import SimulationRequest
from app.services.orchestrator import run_pipeline, run_simulation_pipeline

router = APIRouter()


@router.post("/analyze")
async def analyze_user(user: UserInput):
    return await run_pipeline(user)


@router.post("/simulate")
async def simulate_loan(request: SimulationRequest):
    try:
        return await run_simulation_pipeline(request.user, request.simulation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ⭐ CALIFORNIA-SPECIFIC OPTIONS ENDPOINT
@router.get("/options")
async def get_options():
    """
    Returns all California-specific enum values and constants
    that the frontend needs for dropdowns.
    """
    return {
        # ─────────────────────────
        # 🌴 CALIFORNIA LOCATION
        # ─────────────────────────
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

        # ─────────────────────────
        # 💰 FINANCIAL (USD only)
        # ─────────────────────────
        "currencies": [c.value for c in Currency],  # only USD now

        # ─────────────────────────
        # 💼 PROFESSIONAL
        # ─────────────────────────
        "sectors": [s.value for s in CaliforniaSector],
        "professions": [p.value for p in Profession],
        "employment_statuses": [e.value for e in EmploymentStatus],

        # ⭐ California-specific (optional)
        "tech_roles": [t.value for t in TechRole],
        "equity_compensations": [e.value for e in EquityCompensation],
        "company_stages": [c.value for c in CompanyStage],
        "entertainment_roles": [e.value for e in EntertainmentRole],

        # ─────────────────────────
        # ⚙️ PREFERENCES
        # ─────────────────────────
        "risk_profiles": [r.value for r in RiskProfile],
        "horizons": [h.value for h in HorizonGroup],
        "weekly_hours": [w.value for w in WeeklyHours],
        "predefined_interests": PREDEFINED_INTERESTS,
    }


# ⭐ NEW: Info endpoint za defense priču
@router.get("/info")
async def get_system_info():
    """
    System metadata — used by frontend for branding and
    by users to understand system capabilities.
    """
    return {
        "name": "CaliforniaCFO",
        "tagline": "AI Financial Advisor That Actually Knows California",
        "version": "3.0.0",
        "specialization": "California, USA",
        "regions_covered": len(REGION_DATA),
        "cities_covered": sum(len(data["cities"]) for data in REGION_DATA.values()),
        "features": [
            "Multi-agent investment analysis (Stock, Real Estate, Business)",
            "California-specific tax calculations (Prop 13, QSBS, state tax)",
            "Region-aware risk scoring (8 California regions)",
            "Cost-of-living adjusted financial planning",
            "Live market data via web search (Phase 2)",
            "RAG-based California expert knowledge (Phase 3)",
        ],
        "supported_industries": [
            s.value for s in CaliforniaSector
        ],
    }