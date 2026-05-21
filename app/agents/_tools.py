# app/agents/_tools.py

"""
Function calling tools for agents.
Used ONLY in stock_agent (deterministic ETF allocation).
"""


# ─────────────────────────
# 🛠️ TOOL IMPLEMENTATIONS
# ─────────────────────────

def calculate_stock_allocation(risk_profile: str, horizon: str) -> dict:
    """
    Calculates ETF allocation based on risk profile and investment horizon.

    Returns percentages of diversified ETFs.

    Args:
    risk_profile: low | medium | high
    horizon: 1-3 | 3-5 | 5-8 | 8+ (years)

    Returns:
    Dict with ticker:percentage pairs
    """
    risk = risk_profile.lower()

    # Short horizon (1-3) → konzervativnije bez obzira na risk
    if horizon == "1-3":
        if risk == "low":
            return {
                "BND": "50%",
                "VOO": "20%",
                "SCHD": "20%",
                "Cash reserve": "10%"
            }
        elif risk == "medium":
            return {
                "BND": "35%",
                "VOO": "35%",
                "SCHD": "20%",
                "Cash reserve": "10%"
            }
        else:  # high
            return {
                "VOO": "40%",
                "BND": "25%",
                "QQQ": "20%",
                "VXUS": "10%",
                "Cash reserve": "5%"
            }

    # Medium horizon (3-5)
    elif horizon == "3-5":
        if risk == "low":
            return {
                "VOO": "35%",
                "BND": "30%",
                "SCHD": "20%",
                "VXUS": "10%",
                "Cash reserve": "5%"
            }
        elif risk == "medium":
            return {
                "VOO": "40%",
                "VXUS": "20%",
                "BND": "20%",
                "SCHD": "15%",
                "Cash reserve": "5%"
            }
        else:  # high
            return {
                "QQQ": "30%",
                "VOO": "25%",
                "ARKK": "20%",
                "VXUS": "15%",
                "Cash reserve": "10%"
            }

    # Long horizon (5-8 ili 8+)
    else:
        if risk == "low":
            return {
                "VOO": "40%",
                "VXUS": "20%",
                "SCHD": "20%",
                "BND": "15%",
                "Cash reserve": "5%"
            }
        elif risk == "medium":
            return {
                "VOO": "45%",
                "VXUS": "25%",
                "QQQ": "15%",
                "BND": "10%",
                "Cash reserve": "5%"
            }
        else:  # high
            return {
                "QQQ": "35%",
                "VOO": "25%",
                "ARKK": "20%",
                "EEM": "15%",
                "Cash reserve": "5%"
            }


def calculate_expected_return(risk_profile: str, horizon: str) -> dict:
    """
    Calculates expected return and risk/stability metrics for a stock portfolio.
    Based on historical ETF data.
    """
    risk = risk_profile.lower()

    # Lookup tabela: (return, risk, stability)
    metrics = {
        ("low", "1-3"): (0.045, 0.25, 0.85),
        ("low", "3-5"): (0.055, 0.30, 0.82),
        ("low", "5-8"): (0.065, 0.35, 0.80),
        ("low", "8+"): (0.070, 0.35, 0.80),

        ("medium", "1-3"): (0.060, 0.40, 0.70),
        ("medium", "3-5"): (0.075, 0.45, 0.65),
        ("medium", "5-8"): (0.085, 0.50, 0.65),
        ("medium", "8+"): (0.090, 0.50, 0.65),

        ("high", "1-3"): (0.085, 0.65, 0.50),
        ("high", "3-5"): (0.110, 0.70, 0.45),
        ("high", "5-8"): (0.130, 0.75, 0.45),
        ("high", "8+"): (0.140, 0.75, 0.45),
    }

    expected_return, risk_score, stability = metrics.get(
        (risk, horizon),
        (0.07, 0.5, 0.6)  # default
    )

    return {
        "expected_return": expected_return,
        "risk": risk_score,
        "stability": stability,
    }


# ─────────────────────────
# 📋 TOOL SCHEMAS (OpenAI format)
# ─────────────────────────

STOCK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_stock_allocation",
            "description": (
                "Calculates ETF portfolio allocation based on risk profile and investment horizon. "
                "Returns specific tickers and percentages. "
                "Use this BEFORE generating allocation in JSON output. "
                "DO NOT make up your own ETF percentages — use this tool for accuracy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_profile": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "User's investment risk tolerance"
                    },
                    "horizon": {
                        "type": "string",
                        "enum": ["1-3", "3-5", "5-8", "8+"],
                        "description": "Investment horizon in years"
                    }
                },
                "required": ["risk_profile", "horizon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_expected_return",
            "description": (
                "Returns historically-based expected_return, risk, and stability metrics "
                "for a stock portfolio. Use this for accurate financial metrics. "
                "DO NOT estimate these values yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_profile": {
                        "type": "string",
                        "enum": ["low", "medium", "high"]
                    },
                    "horizon": {
                        "type": "string",
                        "enum": ["1-3", "3-5", "5-8", "8+"]
                    }
                },
                "required": ["risk_profile", "horizon"]
            }
        }
    }
]

# ─────────────────────────
# 🎯 TOOL DISPATCHER
# ─────────────────────────

TOOL_REGISTRY = {
    "calculate_stock_allocation": calculate_stock_allocation,
    "calculate_expected_return": calculate_expected_return,
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Executes the tool by name with arguments."""
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        func = TOOL_REGISTRY[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
