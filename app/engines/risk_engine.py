# app/engines/risk_engine.py

from app.models.user import UserInput
from app.core.california_config import (
    CaliforniaRegion, REGION_DATA, get_region_data
)

# ─────────────────────────
# 🌴 CALIFORNIA REGION FACTORS
# (replaces COUNTRY_RISK)
# ─────────────────────────

# Lower factor = better (less risky for bank)
REGION_RISK_FACTORS = {
    CaliforniaRegion.BAY_AREA: 0.85,  # High income, but high COL
    CaliforniaRegion.ORANGE_COUNTY: 0.90,  # Affluent, stable
    CaliforniaRegion.SAN_DIEGO: 0.95,  # Stable, military presence
    CaliforniaRegion.LOS_ANGELES: 1.00,  # Average baseline
    CaliforniaRegion.SACRAMENTO: 1.00,  # Stable govt jobs
    CaliforniaRegion.CENTRAL_COAST: 1.05,  # Tourism dependent
    CaliforniaRegion.INLAND_EMPIRE: 1.10,  # Lower income
    CaliforniaRegion.CENTRAL_VALLEY: 1.15,  # Agriculture seasonal
}


def calculate_risk_score(user: UserInput) -> dict:
    """
    California-specific risk scoring.
    Considers region cost-of-living, industry premiums, and standard factors.
    """
    score = 0

    region = user.location.region
    region_data = get_region_data(region)
    col_index = region_data["cost_of_living_index"]
    primary_industries = region_data["primary_industries"]

    # ─────────────────────────
    # 💰 DISPOSABLE INCOME
    # (adjusted for California cost of living)
    # ─────────────────────────
    income = user.financial.income
    expenses = user.financial.expenses
    disposable = income - expenses

    # California COL adjustment — in SF $1000 disposable is much less than in Fresno
    real_disposable = disposable / col_index

    if real_disposable > 2000:
        score += 3
    elif real_disposable > 1000:
        score += 2
    elif real_disposable > 500:
        score += 1
    else:
        score += 0

    # ─────────────────────────
    # 💰 SAVINGS (also COL-adjusted)
    # ─────────────────────────
    savings = user.financial.savings
    real_savings = savings / col_index

    if real_savings > 30000:
        score += 3
    elif real_savings > 10000:
        score += 2
    elif real_savings > 3000:
        score += 1
    else:
        score += 0

    # ─────────────────────────
    # 📉 DEBT RATIO
    # ─────────────────────────
    debt = user.financial.monthly_debt
    debt_ratio = debt / income if income > 0 else 1

    if debt_ratio < 0.2:
        score += 3
    elif debt_ratio < 0.35:
        score += 2
    elif debt_ratio < 0.5:
        score += 0
    else:
        score -= 1

    # ─────────────────────────
    # 💼 EMPLOYMENT STATUS
    # ─────────────────────────
    status = user.professional.employment_status

    if status.name == "FULL_TIME":
        score += 3
    elif status.name == "SELF_EMPLOYED":
        score += 2  # CA has many self-employed (entertainment, tech consultants)
    elif status.name == "PART_TIME":
        score += 2
    elif status.name == "FREELANCER":
        score += 1
    else:  # unemployed, student, retired
        score -= 1

    # ─────────────────────────
    # 👤 AGE
    # ─────────────────────────
    age = user.personal.age

    if age < 22:
        score -= 2
    elif 22 <= age <= 24:
        score += 0
    elif 25 <= age <= 55:
        score += 2
    elif 56 <= age <= 64:
        score += 1
    elif age > 65:
        score -= 2

    # ─────────────────────────
    # 🏭 CALIFORNIA INDUSTRY PREMIUM/PENALTY
    # ─────────────────────────
    industry_adjustment = _calculate_industry_adjustment(user, primary_industries)
    score += industry_adjustment

    # ─────────────────────────
    # 💎 EQUITY COMPENSATION BONUS
    # (Tech workers with ISO/RSU often have higher net worth)
    # ─────────────────────────
    equity_bonus = 0
    if user.professional.equity_compensation:
        from app.models.user import EquityCompensation
        if user.professional.equity_compensation in (
                EquityCompensation.RSU,
                EquityCompensation.ISO,
                EquityCompensation.FOUNDER_STOCK,
                EquityCompensation.MIXED,
        ):
            equity_bonus = 1
            score += equity_bonus

    # ─────────────────────────
    # 🌴 CALIFORNIA REGION FACTOR
    # ─────────────────────────
    region_factor = REGION_RISK_FACTORS.get(region, 1.0)
    adjusted_score = score * (1 / region_factor)

    # ─────────────────────────
    # 🔥 FINAL RISK LEVEL (CREDITWORTHINESS)
    # ─────────────────────────
    if adjusted_score >= 12:
        level = "low_risk"
        creditworthiness = "high"
    elif adjusted_score >= 8:
        level = "medium_risk"
        creditworthiness = "medium"
    else:
        level = "high_risk"
        creditworthiness = "low"

    # ─────────────────────────
    # 📊 OUTPUT (backward compatible + California enrichments)
    # ─────────────────────────
    return {
        "base_score": score,
        "adjusted_score": round(adjusted_score, 2),
        "level": level,
        "creditworthiness": creditworthiness,

        # California-specific enrichments
        "region": region.value,
        "region_display_name": region_data["display_name"],
        "region_factor": region_factor,
        "cost_of_living_index": col_index,
        "real_disposable_income": round(real_disposable, 2),
        "real_savings": round(real_savings, 2),

        # Standard outputs
        "disposable_income": disposable,
        "debt_ratio": round(debt_ratio, 2),
        "industry_adjustment": industry_adjustment,
        "equity_bonus": equity_bonus,

        # Legacy field for backward compat
        "country": "US",
        "country_factor": region_factor,
    }


def _calculate_industry_adjustment(user: UserInput, primary_industries: list[str]) -> int:
    """
    California-specific industry premiums/penalties.

    +5 = Bay Area tech (highest stability + comp)
    +3 = Stable industries in matching region
    +0 = Generic match
    -2 = Volatile industries (entertainment, agriculture)
    """
    from app.models.user import CaliforniaSector

    sector = user.professional.sector
    region = user.location.region

    adjustment = 0

    # 🏆 Bay Area + Tech = top combination
    if region == CaliforniaRegion.BAY_AREA and sector == CaliforniaSector.TECHNOLOGY:
        adjustment += 5

    # 🧬 Biotech + San Diego = strong match
    elif region == CaliforniaRegion.SAN_DIEGO and sector == CaliforniaSector.BIOTECHNOLOGY:
        adjustment += 4

    # 🎬 Entertainment + LA = match but volatile income
    elif region == CaliforniaRegion.LOS_ANGELES and sector == CaliforniaSector.ENTERTAINMENT:
        adjustment -= 2  # High income but volatile

    # 🌾 Agriculture + Central Valley = stable but seasonal
    elif region == CaliforniaRegion.CENTRAL_VALLEY and sector == CaliforniaSector.AGRICULTURE:
        adjustment -= 1  # Seasonal income variance

    # 🏛️ Government + Sacramento = very stable
    elif region == CaliforniaRegion.SACRAMENTO and sector == CaliforniaSector.GOVERNMENT:
        adjustment += 3

    # 🏖️ Tourism + Central Coast/SD = moderate volatility
    elif sector == CaliforniaSector.TOURISM and region in (
            CaliforniaRegion.CENTRAL_COAST, CaliforniaRegion.SAN_DIEGO
    ):
        adjustment -= 1

    # Generic: industry matches primary regional industry
    elif sector.name.lower() in [ind.lower() for ind in primary_industries]:
        adjustment += 2

    return adjustment