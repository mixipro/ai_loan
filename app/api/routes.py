# app/api/routes.py

from fastapi import APIRouter
from app.models.user import UserInput
from app.services.orchestrator import run_pipeline


router = APIRouter()


@router.post("/analyze")
async def analyze_user(user: UserInput):
    return await run_pipeline(user)   # ⭐ await