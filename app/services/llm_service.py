# app/services/llm_service.py

import os
import asyncio
import httpx
import logging
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_TIMEOUT = 60.0
LLM_MAX_TOKENS = 4000

MAX_RETRIES = 2
RETRY_BACKOFF = 1.5


async def call_llm(
        prompt: str = "",
        tools: Optional[List[dict]] = None,
        messages: Optional[List[dict]] = None,
) -> dict:
    """
    Asynchronous OpenRouter API call with optional tools support.

    Args:
    prompt: User prompt (used if messages not provided)
    tools: Optional list of function calling tool schemas
    messages: Optional pre-built message list (for tool result follow-ups)

    Returns:
    FULL response dict from API.
    Caller should access response["choices"][0]["message"] for content/tool_calls.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in .env")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Build messages if not forwarded
    if messages is None:
        messages = [
            {"role": "system", "content": "You are a financial advisor AI."},
            {"role": "user", "content": prompt}
        ]

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": LLM_MAX_TOKENS,
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    last_exception = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
                response = await client.post(OPENROUTER_URL, json=payload, headers=headers)

            if response.status_code == 200:
                return response.json()  # ⭐ Vraća ceo response

            if 400 <= response.status_code < 500:
                raise Exception(f"LLM client error ({response.status_code}): {response.text}")

            raise Exception(f"LLM server error ({response.status_code}): {response.text}")

        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF ** attempt
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {wait:.1f}s..."
                )
                await asyncio.sleep(wait)
                continue

        except Exception as e:
            last_exception = e
            if "server error" in str(e).lower() and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF ** attempt
                logger.warning(
                    f"LLM server error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {wait:.1f}s..."
                )
                await asyncio.sleep(wait)
                continue
            raise

    raise Exception(f"LLM failed after {MAX_RETRIES + 1} attempts. Last error: {last_exception}")


# ─────────────────────────
# 🎯 BACKWARD COMPATIBLE WRAPPER
# ─────────────────────────
async def call_llm_text(prompt: str) -> str:
    """
    Old version — returns only content string.
    For agents who do NOT use tools (business, real_estate, judge).
    """
    response = await call_llm(prompt=prompt)
    return response["choices"][0]["message"]["content"]