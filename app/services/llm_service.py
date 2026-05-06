# app/services/llm_service.py

import os
import httpx
from dotenv import load_dotenv

# učitaj .env
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.4")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_TIMEOUT = 30.0  # seconds


async def call_llm(prompt: str) -> str:
    """
    Asinhroni poziv OpenRouter API-ja.
    Koristi httpx.AsyncClient za non-blocking HTTP.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in .env")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a financial advisor AI."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        response = await client.post(OPENROUTER_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"LLM error: {response.text}")

    return response.json()["choices"][0]["message"]["content"]