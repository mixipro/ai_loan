# app/services/orchestrator.py

from app.engines.risk_engine import calculate_risk_score
from app.engines.interest_engine import calculate_interest_rate

import logging

logger = logging.getLogger(__name__)


def run_pipeline(user):
    logger.info("Pipeline started")

    # 🔹 primer pristupa podacima
    income = user.financial.income
    expenses = user.financial.expenses
    savings = user.financial.savings
    country = user.location.country
    city = user.location.city

    disposable_income = income - expenses

    result = {
        "summary": {
            "country": country,
            "city": city,
            "income": income,
            "expenses": expenses,
            "disposable_income": disposable_income,
            "savings": savings
        },
        "status": "Pipeline working"
    }

    logger.info("Pipeline finished")

    return result