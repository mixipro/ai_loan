"""
Loan offers endpoint — returns max loan amounts for 3 loan types
without running any LLM agents. Used by frontend to populate sliders.

Handles both approved and rejected loans gracefully.
Enforces practical minimums to avoid nonsensical tiny loans.
"""

from fastapi import APIRouter, HTTPException
from app.models.user import UserInput
from app.engines import risk_engine, interest_engine, loan_engine

router = APIRouter()


# ⭐ Practical minimum loan amounts (below these, loans are uneconomical)
LOAN_MIN_AMOUNTS = {
    "business": 10000,     # $10k min — LLC fee $800 + working capital
    "mortgage": 50000,     # $50k min — even cheap markets need this
    "margin": 5000,        # $5k min — below this, brokerage fees eat returns
}

# ⭐ Practical max years (override engine 999 for margin)
LOAN_MAX_YEARS_CAP = {
    "business": 10,
    "mortgage": 30,
    "margin": 10,          # ⭐ Cap margin from 999 → 10 years (UI sanity)
}


def _build_loan_offer(
    loan_data: dict,
    rate_data: dict,
    loan_type: str,
    description: str,
    default_years_fallback: int,
    min_years: int,
    extra_fields: dict = None,
) -> dict:
    """
    Safely builds a loan offer, handling both approved and rejected loans.

    Enforces practical minimum amounts (LOAN_MIN_AMOUNTS) to avoid
    nonsensical tiny loans like $2,922 business loans.
    """
    approved = loan_data.get("approved", False)
    max_amount = loan_data.get("max_loan_amount", 0) if approved else 0

    # ⭐ Apply practical minimum threshold
    min_threshold = LOAN_MIN_AMOUNTS.get(loan_type, 0)
    if approved and max_amount < min_threshold:
        approved = False
        rejection_reason = (
            f"Max approved amount (${max_amount:.0f}) is below the practical "
            f"minimum of ${min_threshold:,} for this loan type."
        )
        max_amount = 0
        monthly_payment = 0
    else:
        rejection_reason = loan_data.get("reason", "")
        monthly_payment = loan_data.get("monthly_payment", 0) if approved else 0

    # ⭐ Cap max_years at practical level (margin engine returns 999)
    max_years_cap = LOAN_MAX_YEARS_CAP.get(loan_type, 30)
    raw_max_years = rate_data.get("max_years", default_years_fallback)
    max_years = min(raw_max_years, max_years_cap)

    offer = {
        "loan_type": loan_type,
        "description": description,
        "approved": approved,
        "max_amount": max_amount,
        "interest_rate": rate_data.get("interest_rate", 0),
        "default_years": loan_data.get("loan_years", default_years_fallback),
        "max_years": max_years,
        "min_years": min_years,
        "dti_limit": rate_data.get("dti_limit", 0),
        "monthly_payment_at_max": monthly_payment,
    }

    # Add rejection reason if loan was rejected
    if not approved:
        offer["rejection_reason"] = rejection_reason or (
            "Insufficient income, savings, or DTI capacity for this loan type."
        )

    # Merge extra fields (e.g., min_down_payment_pct for mortgage, max_ltv for margin)
    if extra_fields:
        offer.update(extra_fields)

    return offer


@router.post("/loan-offers")
async def get_loan_offers(user: UserInput) -> dict:
    """
    Returns 3 loan offers + risk profile for the user.

    Fast endpoint (~100ms) — does NOT call LLM agents.
    Used by frontend to populate strategy configurators.
    """
    try:
        # 1. Compute risk profile
        risk = risk_engine.calculate_risk_score(user)

        # 2. Compute interest rates for all loan types
        all_rates = interest_engine.calculate_all_loan_rates(risk)

        # 3. Compute max loan amounts for the 3 active loan types
        all_loans = loan_engine.calculate_all_strategy_loans(user, risk, all_rates)

        # 4. Return user-facing 3 loan offers (skip personal & sbloc)
        return {
            "user_summary": {
                "region": user.location.region.value,
                "city": user.location.city,
                "savings": user.financial.savings,
                "risk_profile": user.preferences.risk_profile.value,
                "horizon": user.preferences.horizon.value,
            },
            "risk": {
                "score": risk.get("adjusted_score", risk.get("base_score", 0)),
                "level": risk["level"],
                "creditworthiness": risk["creditworthiness"],
                "region_display_name": risk["region_display_name"],
                "region_factor": risk["region_factor"],
                "cost_of_living_index": risk["cost_of_living_index"],
                "industry_adjustment": risk["industry_adjustment"],
                "equity_bonus": risk["equity_bonus"],
            },
            "loan_offers": {
                "business": _build_loan_offer(
                    loan_data=all_loans.get("business", {}),
                    rate_data=all_rates.get("business", {}),
                    loan_type="business",
                    description="Business loan for startup or operations",
                    default_years_fallback=7,
                    min_years=1,
                ),
                "mortgage": _build_loan_offer(
                    loan_data=all_loans.get("real_estate", {}),
                    rate_data=all_rates.get("mortgage", {}),
                    loan_type="mortgage",
                    description="30-year fixed mortgage for real estate",
                    default_years_fallback=30,
                    min_years=15,
                    extra_fields={"min_down_payment_pct": 0.20},
                ),
                "margin": _build_loan_offer(
                    loan_data=all_loans.get("stock_margin", {}),
                    rate_data=all_rates.get("margin", {}),
                    loan_type="margin",
                    description="Margin loan for stocks (callable — broker can force liquidation)",
                    default_years_fallback=5,
                    min_years=1,
                    extra_fields={
                        "max_ltv": 0.50,
                        "warning": "Margin investing is risky — broker can force sell if portfolio drops",
                    },
                ),
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loan offers calculation failed: {str(e)}")