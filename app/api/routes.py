# app/api/routes.py

from fastapi import APIRouter
from app.models.user import UserInput
from app.services.orchestrator import run_pipeline

router = APIRouter()

@router.post("/analyze")
def analyze(user: UserInput):
    return run_pipeline(user)
