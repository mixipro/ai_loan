import asyncio

from app.agents import judge_agent


def test_personalized_score_uses_profile_weights():
    strategy = {
        "real_return": 0.1,
        "stability": 0.8,
        "risk": 0.2,
    }

    low_score = judge_agent.personalized_score(strategy, "low")
    high_score = judge_agent.personalized_score(strategy, "high")

    assert low_score == 0.66
    assert high_score == 0.31


def test_select_best_strategy_chooses_best_profitable_strategy():
    strategies = [
        {
            "agent": "stock",
            "status": "profitable",
            "real_return": 0.08,
            "stability": 0.65,
            "risk": 0.45,
            "score": 0.5,
        },
        {
            "agent": "business",
            "status": "profitable",
            "real_return": 0.18,
            "stability": 0.45,
            "risk": 0.7,
            "score": 0.7,
        },
        {
            "agent": "real_estate",
            "status": "unprofitable",
            "real_return": 0.04,
            "stability": 0.8,
            "risk": 0.3,
            "score": 0.4,
        },
    ]

    chosen = judge_agent.select_best_strategy(strategies, "high")

    assert chosen["agent"] == "business"
    assert "personalized_score" in chosen


def test_select_best_strategy_avoids_loan_when_none_profitable():
    strategies = [
        {
            "agent": "stock",
            "status": "unprofitable",
            "real_return": 0.05,
            "stability": 0.7,
            "risk": 0.4,
            "score": 0.5,
        },
        {
            "agent": "real_estate",
            "status": "unprofitable",
            "real_return": 0.03,
            "stability": 0.9,
            "risk": 0.2,
            "score": 0.6,
        },
    ]

    chosen = judge_agent.select_best_strategy(strategies, "low")

    assert chosen["loan_recommendation"] == "AVOID_LOAN"
    assert "No strategy is profitable" in chosen["warning"]


def test_run_judge_agent_returns_fallback_when_no_strategies(
    sample_user,
    approved_loan,
):
    result = asyncio.run(
        judge_agent.run_judge_agent(sample_user, approved_loan, [])
    )

    assert result == {
        "recommended": None,
        "reasoning": "No valid strategies available.",
        "next_step": "Improve financial profile and try again.",
        "comparison": "",
        "profile_used": "medium",
    }


def test_run_judge_agent_uses_generated_explanation(
    monkeypatch,
    sample_user,
    approved_loan,
):
    strategies = [
        {
            "agent": "stock",
            "title": "Balanced ETF Portfolio",
            "status": "profitable",
            "real_return": 0.08,
            "net_return": 0.03,
            "stability": 0.65,
            "risk": 0.45,
            "score": 0.5,
            "pros": [],
            "cons": [],
            "next_steps": ["Open broker account"],
        }
    ]

    async def fake_generate_explanation(user, loan, all_strategies, chosen):
        return {
            "reasoning": "Mocked reasoning",
            "next_step": "Mocked next step",
            "comparison": "Mocked comparison",
        }

    monkeypatch.setattr(
        judge_agent,
        "generate_explanation",
        fake_generate_explanation,
    )

    result = asyncio.run(
        judge_agent.run_judge_agent(sample_user, approved_loan, strategies)
    )

    assert result["recommended"]["agent"] == "stock"
    assert result["reasoning"] == "Mocked reasoning"
    assert result["next_step"] == "Mocked next step"
    assert result["comparison"] == "Mocked comparison"
    assert result["profile_used"] == "medium"
