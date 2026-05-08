# app/api/routes.py

from fastapi import APIRouter, HTTPException
from app.models.user import (
    UserInput, Country, Currency, Sector, Profession,
    EmploymentStatus, RiskProfile, HorizonGroup, WeeklyHours,
    CITIES_BY_COUNTRY, PREDEFINED_INTERESTS
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


# ⭐ NOVI ENDPOINT — frontend dropdown options
@router.get("/options")
async def get_options():
    """
    Vraća sve enum vrednosti i konstante koje frontend treba za dropdown-ove.
    """
    return {
        "countries": [
            {"code": c.value, "name": c.name.replace("_", " ").title()}
            for c in Country
        ],
        "cities_by_country": CITIES_BY_COUNTRY,
        "currencies": [c.value for c in Currency],
        "sectors": [s.value for s in Sector],
        "professions": [p.value for p in Profession],
        "employment_statuses": [e.value for e in EmploymentStatus],
        "risk_profiles": [r.value for r in RiskProfile],
        "horizons": [h.value for h in HorizonGroup],
        "weekly_hours": [w.value for w in WeeklyHours],
        "predefined_interests": PREDEFINED_INTERESTS,
    }