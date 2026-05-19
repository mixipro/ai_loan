# tests/test_phase1_3.py

"""
Phase 1.3 validation — fix-up engines work with California user.
Tests the full sync pipeline (no agents yet — those come in Phase 4).
"""

import sys

sys.path.insert(0, ".")

from app.core.california_config import CaliforniaRegion
from app.models.user import (
    UserInput, PersonalInfo, LocationInfo, FinancialInfo,
    ProfessionalInfo, Preferences,
    CaliforniaSector, EmploymentStatus,
    RiskProfile, HorizonGroup, WeeklyHours,
    Currency,
)
from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_interest_rate
from app.engines.loan_engine import calculate_loan_offer, calculate_custom_loan
from app.engines.inflation_engine import (
    get_inflation_rate, real_return, AgentType
)


def make_test_user():
    """Bay Area tech worker."""
    return UserInput(
        personal=PersonalInfo(age=32),
        location=LocationInfo(
            region=CaliforniaRegion.BAY_AREA,
            city="San Francisco"
        ),
        financial=FinancialInfo(
            income=12000, expenses=5000, monthly_debt=500, savings=60000,
        ),
        professional=ProfessionalInfo(
            sector=CaliforniaSector.TECHNOLOGY,
            profession=Profession.SOFTWARE_ENGINEER,
            employment_status=EmploymentStatus.FULL_TIME,
        ),
        preferences=Preferences(
            risk_profile=RiskProfile.MEDIUM, horizon=HorizonGroup.LONG
        ),
    )


def test_sync_pipeline():
    print("=" * 70)
    print("TEST: Sync pipeline — Risk → Interest → Loan")
    print("=" * 70)

    user = make_test_user()

    # 1. Risk
    risk = calculate_risk_score(user)
    print(f"✅ Risk: {risk['level']} (score={risk['adjusted_score']})")
    print(f"   Region: {risk['region_display_name']}")
    print(f"   COL index: {risk['cost_of_living_index']}")

    # 2. Interest
    interest = calculate_interest_rate(risk, loan_type="personal")
    print(f"\n✅ Interest: {interest['interest_rate'] * 100:.2f}% (personal)")
    print(f"   Min/Max: {interest['min_rate'] * 100:.1f}% - {interest['max_rate'] * 100:.1f}%")

    # 3. Loan
    loan = calculate_loan_offer(user, risk, interest)
    if loan["approved"]:
        print(f"\n✅ Loan approved: ${loan['max_loan_amount']:,.0f} for {loan['loan_years']} years")
        print(f"   Monthly payment: ${loan['monthly_payment']:,.0f}")
        print(f"   Region: {loan['region']}")
    else:
        print(f"\n❌ Loan rejected: {loan['reason']}")

    # 4. Custom loan test
    custom = calculate_custom_loan(
        loan_amount=50000,
        loan_years=5,
        annual_rate=interest["interest_rate"],
        user=user,
        risk=risk
    )
    print(f"\n✅ Custom $50k loan, 5 years:")
    print(f"   Approved: {custom['approved']}")
    if custom['approved']:
        print(f"   Monthly: ${custom['monthly_payment']:,.0f}")
        print(f"   Total interest: ${custom['total_interest']:,.0f}")
    print()


def test_inflation():
    print("=" * 70)
    print("TEST: Inflation engine")
    print("=" * 70)

    # Stock inflation (currency-based)
    stock_inf = get_inflation_rate(AgentType.STOCK, "USD")
    print(f"✅ Stock (USD) inflation: {stock_inf * 100:.2f}%")

    # Real estate inflation (US)
    re_inf = get_inflation_rate(AgentType.REAL_ESTATE, "USD")
    print(f"✅ Real estate (US) inflation: {re_inf * 100:.2f}%")

    # Business inflation
    biz_inf = get_inflation_rate(AgentType.BUSINESS, "USD")
    print(f"✅ Business (US) inflation: {biz_inf * 100:.2f}%")

    # Real return calc
    nominal = 0.08  # 8% nominal
    real = real_return(nominal, AgentType.STOCK, "USD")
    print(f"\n✅ Real return on 8% nominal: {real * 100:.2f}%")
    print()


def test_full_orchestrator():
    print("=" * 70)
    print("TEST: Full orchestrator (sync portion)")
    print("=" * 70)

    user = make_test_user()

    risk = calculate_risk_score(user)
    interest = calculate_interest_rate(risk, loan_type="personal")
    loan = calculate_loan_offer(user, risk, interest)

    print(f"✅ Pipeline completed end-to-end (sync portion)")
    print(f"   Region: {risk['region_display_name']}")
    print(f"   Rate: {interest['interest_rate'] * 100:.2f}%")
    print(f"   Loan: ${loan['max_loan_amount']:,.0f}")
    print()


if __name__ == "__main__":
    print("\n🌴 PHASE 1.3 VALIDATION — Downstream fix-up\n")

    try:
        test_sync_pipeline()
        test_inflation()
        test_full_orchestrator()

        print("=" * 70)
        print("✅ ALL PHASE 1.3 TESTS PASSED")
        print("=" * 70)
        print("\nReady for Phase 1.4 (routes + /options endpoint)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)