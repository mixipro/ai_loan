"""
tests/unit/test_risk_score_california.py

Risk score tests for California-only model (replaces tests/engines/test_risk_engine.py
which referenced the removed Country enum).

Backend returns these keys (verified May 2026):
  base_score, adjusted_score, level, creditworthiness, region,
  region_display_name, region_factor, cost_of_living_index,
  real_disposable_income, real_savings, disposable_income,
  debt_ratio, industry_adjustment, equity_bonus, country, country_factor
"""

import pytest

from app.engines.risk_engine import calculate_risk_score
from app.models.user import (
    FinancialInfo,
    LocationInfo,
    PersonalInfo,
    Preferences,
    ProfessionalInfo,
    UserInput,
)


def make_user(
    income: float = 8000,
    expenses: float = 4000,
    monthly_debt: float = 500,
    savings: float = 100_000,
    region: str = "BAY_AREA",
    city: str = "San Francisco",
    risk_profile: str = "medium",
) -> UserInput:
    """Helper: build a UserInput for risk-score tests."""
    return UserInput(
        personal=PersonalInfo(age=35),
        location=LocationInfo(region=region, city=city),
        financial=FinancialInfo(
            income=income,
            expenses=expenses,
            monthly_debt=monthly_debt,
            savings=savings,
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
        preferences=Preferences(risk_profile=risk_profile, horizon="5-8"),
    )


class TestRiskScoreShape:
    """Risk score returns a dict with expected keys."""

    def test_returns_dict(self):
        user = make_user()
        result = calculate_risk_score(user)
        assert isinstance(result, dict)

    def test_has_base_score_field(self):
        """Backend uses 'base_score' and 'adjusted_score', not generic 'score'."""
        user = make_user()
        result = calculate_risk_score(user)
        assert "base_score" in result
        assert isinstance(result["base_score"], (int, float))

    def test_has_adjusted_score_field(self):
        user = make_user()
        result = calculate_risk_score(user)
        assert "adjusted_score" in result
        assert isinstance(result["adjusted_score"], (int, float))

    def test_has_level_field(self):
        user = make_user()
        result = calculate_risk_score(user)
        assert "level" in result
        assert result["level"] in {"low_risk", "medium_risk", "high_risk"}

    def test_has_creditworthiness_field(self):
        user = make_user()
        result = calculate_risk_score(user)
        assert "creditworthiness" in result

    def test_has_region_info(self):
        user = make_user()
        result = calculate_risk_score(user)
        assert "region" in result
        assert "region_display_name" in result
        assert "region_factor" in result


class TestRiskScoreSensitivity:
    """Score should react to financial inputs."""

    def test_low_dti_better_than_high_dti(self):
        """Lower debt-to-income ratio → lower (better) debt_ratio."""
        low_dti = make_user(income=10_000, monthly_debt=200)
        high_dti = make_user(income=10_000, monthly_debt=5_000)

        low_result = calculate_risk_score(low_dti)
        high_result = calculate_risk_score(high_dti)

        assert low_result["debt_ratio"] < high_result["debt_ratio"]

    def test_higher_savings_higher_real_savings(self):
        """More savings → higher real_savings figure (inflation-adjusted)."""
        rich = make_user(savings=500_000)
        poor = make_user(savings=10_000)

        rich_result = calculate_risk_score(rich)
        poor_result = calculate_risk_score(poor)

        assert rich_result["real_savings"] > poor_result["real_savings"]


class TestRegionalAdjustment:
    """California regions should yield reasonable risk metrics."""

    @pytest.mark.parametrize(
        "region,city",
        [
            ("BAY_AREA", "San Francisco"),
            ("LOS_ANGELES", "Long Beach"),
            ("SAN_DIEGO", "Chula Vista"),
            ("SACRAMENTO", "Sacramento"),
            ("INLAND_EMPIRE", "Riverside"),
        ],
    )
    def test_all_regions_return_valid_score(self, region, city):
        """Use proper city for each region (Long Beach for LA, etc.)."""
        user = make_user(region=region, city=city)
        result = calculate_risk_score(user)

        assert result["level"] in {"low_risk", "medium_risk", "high_risk"}
        assert "base_score" in result
        assert "adjusted_score" in result
        assert result["region"] == region

    def test_bay_area_has_high_cost_of_living_index(self):
        """Bay Area should have a higher cost-of-living index than Sacramento."""
        ba = make_user(region="BAY_AREA", city="San Francisco")
        sac = make_user(region="SACRAMENTO", city="Sacramento")

        ba_result = calculate_risk_score(ba)
        sac_result = calculate_risk_score(sac)

        # COL index: Bay Area ~1.85, Sacramento ~lower
        assert ba_result["cost_of_living_index"] >= sac_result["cost_of_living_index"]

    def test_real_disposable_income_calculated(self):
        """Real disposable income should be positive for solid user."""
        user = make_user()
        result = calculate_risk_score(user)
        assert "real_disposable_income" in result
        assert result["real_disposable_income"] > 0
