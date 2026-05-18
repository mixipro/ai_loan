# app/models/analyze.py
"""
Request models for /analyze endpoint.

User must POST per-strategy configuration along with their profile.
Each strategy has its own loan + savings allocation, set via UI sliders.
"""

from pydantic import BaseModel, Field
from app.models.user import UserInput


class StrategyConfig(BaseModel):
    """
    Per-strategy capital allocation configuration.

    For all 3 strategies (business, real_estate, stock):
    - loan_amount: 0 = cash-only; > 0 = with loan
    - savings_to_use: amount of savings to allocate to this strategy
    - loan_years: term length
    - interest_rate: from /loan-offers

    For real_estate: savings_to_use must be ≥ 20% of (loan_amount + savings_to_use)
                     loan_amount must be > 0 (mortgage required)
    For stock: loan_amount ≤ savings_to_use (50% LTV max — auto-capped if higher)
    """
    loan_amount: float = Field(default=0, ge=0)
    loan_years: int = Field(default=0, ge=0, le=30)
    savings_to_use: float = Field(default=0, ge=0)
    interest_rate: float = Field(default=0, ge=0, le=0.30)


class AnalyzeConfig(BaseModel):
    """Configuration for all 3 strategies."""
    business: StrategyConfig
    real_estate: StrategyConfig
    stock: StrategyConfig


class AnalyzeRequest(BaseModel):
    """Full request body for POST /analyze."""
    user: UserInput
    config: AnalyzeConfig