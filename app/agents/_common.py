# app/agents/_common.py

import json
import asyncio
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# ⭐ Retry config za JSON parsing failures
JSON_PARSE_RETRIES = 2


def clean_llm_json(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return cleaned


def extract_json_from_text(text: str) -> str:
    """Vadi JSON region (od { do }) iz teksta."""
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def parse_llm_json(raw: str) -> dict:
    """
    Parsira LLM output kao JSON, sa cleanup-om i fallback ekstrakcijom.
    """
    cleaned = clean_llm_json(raw)

    # Pokušaj 1: direktan parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Pokušaj 2: ekstraktuj JSON region
    try:
        extracted = extract_json_from_text(cleaned)
        return json.loads(extracted)
    except json.JSONDecodeError:
        pass

    raise ValueError(
        f"Invalid LLM output (not valid JSON after cleanup attempts). "
        f"Raw start: {raw[:200]}... "
        f"Length: {len(raw)} chars"
    )


# ⭐ NOVA FUNKCIJA — retry wrapper za LLM + parsing
async def call_llm_with_retry(
        llm_call: Callable[[], Awaitable[str]],
        agent_name: str = "unknown"
) -> dict:
    """
    Poziva LLM funkciju sa retry-jem ako JSON parsing padne.

    Args:
        llm_call: async funkcija koja vraća raw LLM output (string)
        agent_name: ime agenta za logging

    Returns:
        Parsed JSON dict

    Raises:
        ValueError: ako svi pokušaji propadnu
    """
    last_error = None
    last_raw = None

    for attempt in range(JSON_PARSE_RETRIES + 1):  # 0, 1, 2
        try:
            raw = await llm_call()
            last_raw = raw
            return parse_llm_json(raw)
        except ValueError as e:
            last_error = e
            if attempt < JSON_PARSE_RETRIES:
                logger.warning(
                    f"Agent '{agent_name}' JSON parse failed "
                    f"(attempt {attempt + 1}/{JSON_PARSE_RETRIES + 1}): {e}. "
                    f"Retrying with fresh LLM call..."
                )
                await asyncio.sleep(0.5)  # mali wait pre retry-ja
                continue

    # Sve pokušaje smo iscrpli
    raise ValueError(
        f"Agent '{agent_name}' failed after {JSON_PARSE_RETRIES + 1} attempts. "
        f"Last error: {last_error}. "
        f"Last raw output: {last_raw[:300] if last_raw else 'None'}..."
    )


def clamp(value: Any, min_val: float, max_val: float, default: float) -> float:
    if value is None:
        return default
    try:
        v = float(value)
    except (ValueError, TypeError):
        return default
    return min(max(v, min_val), max_val)


def safe_list(value: Any, default: list = None) -> list:
    if default is None:
        default = []
    if isinstance(value, list):
        return value
    return default


def safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def safe_dict(value: Any, default: dict = None) -> dict:
    if default is None:
        default = {}
    if isinstance(value, dict):
        return value
    return default


def validate_allocation(allocation: dict, total_capital: float, agent_name: str) -> dict:
    """
    Proverava da li je allocation suma razumna.
    Ako su sve vrednosti 0 ili suma ne odgovara kapitalu → loguj upozorenje.
    """
    if not allocation:
        return allocation

    # Filtriraj samo numeričke vrednosti (stock ima procente kao strings)
    numeric_values = {}
    for k, v in allocation.items():
        try:
            numeric_values[k] = float(v)
        except (ValueError, TypeError):
            pass  # string procenti (VOO: "40%") — preskoči

    if not numeric_values:
        return allocation  # stock agent sa procentima — OK

    total = sum(numeric_values.values())

    # ⚠️ Sve nule — LLM nije popunio
    if total == 0:
        logger.warning(
            f"Agent '{agent_name}': allocation is all zeros! "
            f"LLM description may have correct values but JSON has zeros."
        )

    # ⚠️ Suma se ne slaže sa kapitalom (tolerancija 10%)
    elif total_capital > 0 and abs(total - total_capital) / total_capital > 0.10:
        logger.warning(
            f"Agent '{agent_name}': allocation sum ({total:.2f}) "
            f"differs from total capital ({total_capital:.2f}) by more than 10%."
        )

    return allocation