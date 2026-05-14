# tests/test_loan_infrastructure.py

import sys

sys.path.insert(0, ".")

from app.core.california_config import CaliforniaRegion
from app.models.user import (
    UserInput, PersonalInfo, LocationInfo, FinancialInfo,
    ProfessionalInfo, Preferences,
    CaliforniaSector, Profession, EmploymentStatus,
    RiskProfile, HorizonGroup, WeeklyHours, Currency,
)
from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_all_loan_rates, LOAN_TYPES
from app.engines.loan_engine import calculate_all_strategy_loans


def make_test_user():
    return UserInput(
        personal=PersonalInfo(age=32),
        location=LocationInfo(region=CaliforniaRegion.BAY_AREA, city="San Francisco"),
        financial=FinancialInfo(income=15000, expenses=5000, monthly_debt=800, savings=80000),
        professional=ProfessionalInfo(
            sector=CaliforniaSector.TECHNOLOGY,
            profession=Profession.SOFTWARE_ENGINEER,
            employment_status=EmploymentStatus.FULL_TIME,
        ),
        preferences=Preferences(risk_profile=RiskProfile.MEDIUM, horizon=HorizonGroup.LONG),
    )


def test_loan_types_defined():
    print("=" * 70)
    print("TEST 1: Loan types defined")
    print("=" * 70)

    expected = {"personal", "business", "mortgage", "margin", "sbloc"}
    actual = set(LOAN_TYPES.keys())

    assert expected == actual, f"Missing: {expected - actual}"
    print(f"✅ All 5 loan types defined: {actual}")

    for name, config in LOAN_TYPES.items():
        print(
            f"   • {name}: {config['rate_range'][0] * 100:.1f}-{config['rate_range'][1] * 100:.1f}%, {config['default_years']}yr, {config['description'][:50]}")
    print()


def test_all_loan_rates():
    print("=" * 70)
    print("TEST 2: All loan rates for Bay Area tech worker")
    print("=" * 70)

    user = make_test_user()
    risk = calculate_risk_score(user)

    print(f"Risk: {risk['level']} (score={risk['adjusted_score']})\n")

    all_rates = calculate_all_loan_rates(risk)

    for loan_type, rate_data in all_rates.items():
        print(
            f"✅ {loan_type:10s}: {rate_data['interest_rate'] * 100:.2f}% ({rate_data['default_years']}y, DTI {rate_data['dti_limit'] * 100:.0f}%)")
    print()


def test_all_strategy_loans():
    print("=" * 70)
    print("TEST 3: All strategy loans")
    print("=" * 70)

    user = make_test_user()
    risk = calculate_risk_score(user)
    all_rates = calculate_all_loan_rates(risk)

    strategy_loans = calculate_all_strategy_loans(user, risk, all_rates)

    for strategy, loan in strategy_loans.items():
        if loan["approved"]:
            print(f"✅ {strategy:15s}: ${loan['max_loan_amount']:>12,.0f} | "
                  f"${loan['monthly_payment']:>7,.0f}/mo | "
                  f"{loan['loan_years']:>2}y | "
                  f"{loan['interest_rate'] * 100:.2f}% | "
                  f"{loan['loan_type']}")
        else:
            print(f"❌ {strategy:15s}: REJECTED - {loan.get('reason')}")
    print()


def test_mortgage_vs_personal():
    print("=" * 70)
    print("TEST 4: Mortgage should give MUCH MORE money than personal loan")
    print("=" * 70)

    user = make_test_user()
    risk = calculate_risk_score(user)
    all_rates = calculate_all_loan_rates(risk)
    strategy_loans = calculate_all_strategy_loans(user, risk, all_rates)

    mortgage = strategy_loans["real_estate"]["max_loan_amount"]
    personal = strategy_loans["personal"]["max_loan_amount"]

    print(f"Personal loan max:  ${personal:>12,.0f}")
    print(f"Mortgage max:       ${mortgage:>12,.0f}")
    print(f"Ratio:              {mortgage / personal:.1f}x")

    assert mortgage > personal * 2, "Mortgage should be at least 2x bigger (longer term)"
    print(f"✅ Mortgage is {mortgage / personal:.1f}x bigger — CORRECT (30yr vs 5yr)")
    print()


def test_margin_loan_ltv():
    print("=" * 70)
    print("TEST 5: Margin loan capped at 50% of savings (LTV rule)")
    print("=" * 70)

    user = make_test_user()  # savings = $80,000
    risk = calculate_risk_score(user)
    all_rates = calculate_all_loan_rates(risk)
    strategy_loans = calculate_all_strategy_loans(user, risk, all_rates)

    margin = strategy_loans["stock_margin"]["max_loan_amount"]
    savings = user.financial.savings

    print(f"Savings:            ${savings:>12,.0f}")
    print(f"Margin loan:        ${margin:>12,.0f}")
    print(f"LTV ratio:          {margin / savings * 100:.1f}%")

    assert margin <= savings * 0.5 + 1, f"Margin should be capped at 50% of savings ({savings * 0.5})"
    print(f"✅ Margin loan respects 50% LTV cap")
    print()


if __name__ == "__main__":
    print("\n🏦 KORAK 1 VALIDATION — Loan Infrastructure\n")

    try:
        test_loan_types_defined()
        test_all_loan_rates()
        test_all_strategy_loans()
        test_mortgage_vs_personal()
        test_margin_loan_ltv()

        print("=" * 70)
        print("✅ ALL KORAK 1 TESTS PASSED")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)