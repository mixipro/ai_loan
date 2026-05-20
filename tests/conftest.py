# tests/conftest.py
#
# Pytest configuration:
# - collect_ignore: legacy pre-California pivot test files that fail to
#   import due to removed Country/EUR enums.
# - Shared fixtures: base_user (current model) + sample_user (legacy alias).

import pytest

# ─── COLLECT IGNORE (pre-California pivot tests) ───
collect_ignore = [
    "engines/test_risk_engine.py",
    "engines/test_interest_engine.py",
    "engines/test_loan_engine.py",
    "engines/test_inflation_engine.py",       # uses RS/EUR — legacy
    "services/test_orchestrator.py",
    "services/test_pipeline.py",
    "manual",                                  # all manual smoke tests (LLM-dependent)
    "historical/test_historical.py",
    "fixtures/test_models_user.py",
    "agents/test_judge_agent.py",             # legacy: judge API changed in v5.2
    "api/test_analyze.py",                    # legacy: response shape changed in v5.2
]


# ─── SHARED FIXTURES ───
def _make_california_user():
    """Construct a minimal valid California UserInput."""
    from app.models.user import (
        FinancialInfo,
        LocationInfo,
        PersonalInfo,
        Preferences,
        ProfessionalInfo,
        UserInput,
    )

    return UserInput(
        personal=PersonalInfo(age=35),
        location=LocationInfo(region="BAY_AREA", city="San Francisco"),
        financial=FinancialInfo(
            income=8000,
            expenses=4000,
            monthly_debt=500,
            savings=100_000,
            currency="USD",
        ),
        professional=ProfessionalInfo(
            sector="Technology",
            profession="Software Engineer",
            employment_status="full-time",
            interests=["investing"],
            prior_experience="",
            weekly_hours="30+",
        ),
        preferences=Preferences(risk_profile="medium", horizon="5-8"),
    )


@pytest.fixture
def base_user():
    """Minimal valid California user for risk/inflation/engine tests."""
    return _make_california_user()


@pytest.fixture
def sample_user():
    """Alias for legacy tests that expect 'sample_user' fixture name."""
    return _make_california_user()
