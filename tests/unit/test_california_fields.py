"""
tests/unit/test_california_fields.py

Unit tests for California-specific professional fields added in Day 5:
- tech_role (FAANG, Big Tech, etc.)
- equity_compensation (RSU, Founder Stock, etc.)
- company_stage (Seed, Series A-B, Public, etc.)
- entertainment_role (Above-the-line, etc.)
"""

import pytest
from pydantic import ValidationError

from app.models.user import (
    FinancialInfo,
    LocationInfo,
    PersonalInfo,
    Preferences,
    ProfessionalInfo,
    UserInput,
)


def make_minimal_user(professional_extra: dict = None) -> UserInput:
    """Helper: minimal valid UserInput, can extend professional block."""
    pro = {
        "sector": "Technology",
        "profession": "Software Engineer",
        "employment_status": "full-time",
        "interests": ["investing"],
        "prior_experience": "",
        "weekly_hours": "30+",
    }
    if professional_extra:
        pro.update(professional_extra)

    return UserInput(
        personal=PersonalInfo(age=30),
        location=LocationInfo(region="BAY_AREA", city="San Francisco"),
        financial=FinancialInfo(
            income=15000,
            expenses=5000,
            monthly_debt=500,
            savings=80000,
            currency="USD",
        ),
        professional=ProfessionalInfo(**pro),
        preferences=Preferences(risk_profile="medium", horizon="5-8"),
    )


# ─── BASE: no California fields ───
def test_user_without_california_fields_is_valid():
    """California fields are OPTIONAL — user can submit without them."""
    user = make_minimal_user()

    assert user.professional.sector == "Technology"
    assert getattr(user.professional, "tech_role", None) is None


# ─── tech_role ───
class TestTechRole:
    def test_valid_tech_role_accepted(self):
        user = make_minimal_user({"tech_role": "Software Engineer"})
        assert user.professional.tech_role == "Software Engineer"

    def test_valid_tech_executive_accepted(self):
        user = make_minimal_user({"tech_role": "Tech Executive (VP/CTO/CEO)"})
        assert user.professional.tech_role == "Tech Executive (VP/CTO/CEO)"

    def test_invalid_tech_role_rejected(self):
        with pytest.raises(ValidationError, match=r"tech_role|enum"):
            make_minimal_user({"tech_role": "FakeRole That Does Not Exist"})


# ─── equity_compensation ───
class TestEquityCompensation:
    def test_rsu_compensation_accepted(self):
        user = make_minimal_user(
            {"equity_compensation": "RSU (Restricted Stock Units)"}
        )
        assert user.professional.equity_compensation == "RSU (Restricted Stock Units)"

    def test_founder_stock_accepted(self):
        user = make_minimal_user({"equity_compensation": "Founder Stock"})
        assert user.professional.equity_compensation == "Founder Stock"

    def test_none_value_accepted(self):
        user = make_minimal_user({"equity_compensation": "None"})
        assert user.professional.equity_compensation == "None"

    def test_invalid_compensation_rejected(self):
        # Common mistake: short form "RSU" instead of full label
        with pytest.raises(ValidationError, match=r"equity_compensation|enum"):
            make_minimal_user({"equity_compensation": "RSU"})


# ─── company_stage ───
class TestCompanyStage:
    def test_seed_stage_accepted(self):
        user = make_minimal_user({"company_stage": "Seed Stage Startup"})
        assert user.professional.company_stage == "Seed Stage Startup"

    def test_faang_accepted(self):
        user = make_minimal_user({"company_stage": "Big Tech / FAANG"})
        assert user.professional.company_stage == "Big Tech / FAANG"

    def test_invalid_stage_rejected(self):
        with pytest.raises(ValidationError, match=r"company_stage|enum"):
            make_minimal_user({"company_stage": "Public/IPO"})


# ─── entertainment_role (for Entertainment sector) ───
class TestEntertainmentRole:
    def test_above_the_line_accepted(self):
        user = make_minimal_user(
            {"entertainment_role": "Above-the-line (Writer/Director/Producer)"}
        )
        assert (
            user.professional.entertainment_role
            == "Above-the-line (Writer/Director/Producer)"
        )

    def test_below_the_line_accepted(self):
        user = make_minimal_user({"entertainment_role": "Below-the-line (Crew)"})
        assert user.professional.entertainment_role == "Below-the-line (Crew)"

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError, match=r"entertainment_role|enum"):
            make_minimal_user({"entertainment_role": "Background Actor"})


# ─── full California Tech profile ───
def test_full_california_tech_profile_valid():
    """Integration: all 3 tech fields together must pass validation."""
    user = make_minimal_user({
        "tech_role": "Software Engineer",
        "equity_compensation": "RSU (Restricted Stock Units)",
        "company_stage": "Big Tech / FAANG",
    })

    assert user.professional.tech_role == "Software Engineer"
    assert user.professional.equity_compensation == "RSU (Restricted Stock Units)"
    assert user.professional.company_stage == "Big Tech / FAANG"
