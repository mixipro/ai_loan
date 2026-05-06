# app/agents/_common.py

import json
from typing import Any


def clean_llm_json(raw: str) -> str:
    """
    Uklanja markdown fences (```json ... ```) iz LLM output-a.
    LLM-ovi često vraćaju JSON umotan u markdown.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return cleaned


def parse_llm_json(raw: str) -> dict:
    """
    Parsira LLM output kao JSON, sa cleanup-om i error handling-om.
    """
    cleaned = clean_llm_json(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid LLM output (not valid JSON): {raw[:200]}")


def clamp(value: Any, min_val: float, max_val: float, default: float) -> float:
    """
    Ograničava vrednost između min i max. Ako je None ili nevalidna → default.
    """
    if value is None:
        return default
    try:
        v = float(value)
    except (ValueError, TypeError):
        return default
    return min(max(v, min_val), max_val)


def safe_list(value: Any, default: list = None) -> list:
    """
    Vraća listu — ako je None ili nije lista, vraća default.
    """
    if default is None:
        default = []
    if isinstance(value, list):
        return value
    return default


def safe_str(value: Any, default: str = "") -> str:
    """
    Vraća string — ako je None ili nije string, vraća default.
    """
    if value is None:
        return default
    return str(value)


def safe_dict(value: Any, default: dict = None) -> dict:
    """
    Vraća dict — ako je None ili nije dict, vraća default.
    """
    if default is None:
        default = {}
    if isinstance(value, dict):
        return value
    return default