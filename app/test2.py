# tests/test_phase1_complete.py

"""
Complete Phase 1 validation:
- California config
- Tax engine
- User models (California-aware)
- Risk engine (California-aware)
"""

import sys

sys.path.insert(0, ".")

from app.core.california_config import REGION_DATA, CaliforniaRegion
from app.models.user import (
    UserInput, PersonalInfo, LocationInfo, FinancialInfo,
    ProfessionalInfo, Preferences,
    CaliforniaSector, Profession, EmploymentStatus,
    RiskProfile, HorizonGroup, WeeklyHours,
    TechRole, EquityCompensation, CompanyStage,
    Currency,
)
from app.engines.risk_engine import calculate_risk_score


def test_california_user_models():
    print("=" * 70)
    print("TEST 1: California User Model")
    print("=" * 70)

    # Bay Area tech worker with QSBS-eligible equity
    user = UserInput(
        personal=PersonalInfo(age=32),
        location=LocationInfo(
            region=CaliforniaRegion.BAY_AREA,
            city="San Francisco"
        ),
        financial=FinancialInfo(
            income=15000,
            expenses=5000,
            monthly_debt=500,
            savings=80000,
            currency=Currency.USD,
        ),
        professional=ProfessionalInfo(
            sector=CaliforniaSector.TECHNOLOGY,
            profession=Profession.SOFTWARE_ENGINEER,
            employment_status=EmploymentStatus.FULL_TIME,
            interests=["ai/ml", "startups", "investing"],
            prior_experience="Built side-project SaaS",
            weekly_hours=WeeklyHours.LIGHT,
            # California-specific fields
            tech_role=TechRole.SOFTWARE_ENGINEER,
            equity_compensation=EquityCompensation.RSU,
            company_stage=CompanyStage.PUBLIC,
        ),
        preferences=Preferences(
            risk_profile=RiskProfile.MEDIUM,
            horizon=HorizonGroup.LONG,
        ),
    )

    print(f"✅ Created Bay Area tech worker")
    print(f"   Region: {user.location.region.value}")
    print(f"   City: {user.location.city}")
    print(f"   Sector: {user.professional.sector.value}")
    print(f"   Tech role: {user.professional.tech_role.value}")
    print(f"   Equity: {user.professional.equity_compensation.value}")
    print()


def test_invalid_city_for_region():
    print("=" * 70)
    print("TEST 2: Invalid City for Region")
    print("=" * 70)

    try:
        LocationInfo(
            region=CaliforniaRegion.BAY_AREA,
            city="Beverly Hills"  # That's LA, not Bay Area
        )
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly rejected: {str(e)[:80]}...")
    print()


def test_risk_score_bay_area_tech():
    print("=" * 70)
    print("TEST 3: Risk Score — Bay Area Tech Worker")
    print("=" * 70)

    user = UserInput(
        personal=PersonalInfo(age=32),
        location=LocationInfo(region=CaliforniaRegion.BAY_AREA, city="San Francisco"),
        financial=FinancialInfo(
            income=15000, expenses=5000, monthly_debt=500, savings=80000
        ),
        professional=ProfessionalInfo(
            sector=CaliforniaSector.TECHNOLOGY,
            profession=Profession.SOFTWARE_ENGINEER,
            employment_status=EmploymentStatus.FULL_TIME,
            equity_compensation=EquityCompensation.RSU,
        ),
        preferences=Preferences(
            risk_profile=RiskProfile.MEDIUM, horizon=HorizonGroup.LONG
        ),
    )

    risk = calculate_risk_score(user)

    print(f"Region: {risk['region_display_name']}")
    print(f"Cost of living: {risk['cost_of_living_index']}x")
    print(f"Real disposable: ${risk['real_disposable_income']:,.0f}")
    print(f"Real savings: ${risk['real_savings']:,.0f}")
    print(f"Industry adjustment: +{risk['industry_adjustment']} (Bay Area Tech!)")
    print(f"Equity bonus: +{risk['equity_bonus']}")
    print(f"Base score: {risk['base_score']}")
    print(f"Adjusted score: {risk['adjusted_score']}")
    print(f"Level: {risk['level']} (creditworthiness: {risk['creditworthiness']})")
    print()


def test_risk_score_central_valley_farmer():
    print("=" * 70)
    print("TEST 4: Risk Score — Central Valley Farmer")
    print("=" * 70)

    user = UserInput(
        personal=PersonalInfo(age=45),
        location=LocationInfo(region=CaliforniaRegion.CENTRAL_VALLEY, city="Fresno"),
        financial=FinancialInfo(
            income=5500, expenses=3000, monthly_debt=200, savings=25000
        ),
        professional=ProfessionalInfo(
            sector=CaliforniaSector.AGRICULTURE,
            profession=Profession.FARMER,
            employment_status=EmploymentStatus.SELF_EMPLOYED,
        ),
        preferences=Preferences(
            risk_profile=RiskProfile.LOW, horizon=HorizonGroup.MEDIUM
        ),
    )

    risk = calculate_risk_score(user)

    print(f"Region: {risk['region_display_name']}")
    print(f"Cost of living: {risk['cost_of_living_index']}x")
    print(f"Real disposable: ${risk['real_disposable_income']:,.0f}")
    print(f"Industry adjustment: {risk['industry_adjustment']} (seasonal income)")
    print(f"Adjusted score: {risk['adjusted_score']}")
    print(f"Level: {risk['level']} (creditworthiness: {risk['creditworthiness']})")
    print()


def test_risk_score_la_actor():
    print("=" * 70)
    print("TEST 5: Risk Score — LA Entertainment Worker")
    print("=" * 70)

    user = UserInput(
        personal=PersonalInfo(age=29),
        location=LocationInfo(region=CaliforniaRegion.LOS_ANGELES, city="Hollywood"),
        financial=FinancialInfo(
            income=8000, expenses=4500, monthly_debt=300, savings=15000
        ),
        professional=ProfessionalInfo(
            sector=CaliforniaSector.ENTERTAINMENT,
            profession=Profession.ACTOR,
            employment_status=EmploymentStatus.FREELANCER,
        ),
        preferences=Preferences(
            risk_profile=RiskProfile.MEDIUM, horizon=HorizonGroup.MEDIUM
        ),
    )

    risk = calculate_risk_score(user)

    print(f"Region: {risk['region_display_name']}")
    print(f"Industry adjustment: {risk['industry_adjustment']} (volatile income)")
    print(f"Adjusted score: {risk['adjusted_score']}")
    print(f"Level: {risk['level']} (creditworthiness: {risk['creditworthiness']})")
    print()


if __name__ == "__main__":
    print("\n🌴 PHASE 1.2 VALIDATION — California User Model + Risk Engine\n")

    try:
        test_california_user_models()
        test_invalid_city_for_region()
        test_risk_score_bay_area_tech()
        test_risk_score_central_valley_farmer()
        test_risk_score_la_actor()

        print("=" * 70)
        print("✅ ALL PHASE 1.2 TESTS PASSED — Ready for Phase 2!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)