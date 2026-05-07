# app/services/llm_service.py

import os
import asyncio
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_TIMEOUT = 60.0
LLM_MAX_TOKENS = 4000

# ⭐ RETRY KONFIGURACIJA
MAX_RETRIES = 2  # ukupno 3 pokušaja (1 + 2 retry)
RETRY_BACKOFF = 1.5  # sekundi između pokušaja (eksponencijalno)


async def call_llm(prompt: str) -> str:
    """
    Asinhroni poziv OpenRouter API-ja sa retry logikom.
    Retry se aktivira na network errors (timeout, 5xx, connection errors).
    NE retry-uje na 4xx (autentifikacija, bad request — to su naše greške).
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
        "temperature": 0.3,
        "max_tokens": LLM_MAX_TOKENS,
    }

    last_exception = None

    for attempt in range(MAX_RETRIES + 1):  # 0, 1, 2
        try:
            async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
                response = await client.post(OPENROUTER_URL, json=payload, headers=headers)

            # 🛡️ Razlikuj retry-able vs non-retry-able errore
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]

            # 4xx = naša greška (auth, bad request) — NEMA retry-ja
            if 400 <= response.status_code < 500:
                raise Exception(f"LLM client error ({response.status_code}): {response.text}")

            # 5xx = server greška — RETRY
            raise Exception(f"LLM server error ({response.status_code}): {response.text}")

        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as e:
            # Network/timeout errors → retry
            last_exception = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF ** attempt  # 1.0, 1.5, 2.25 seconds
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {wait:.1f}s..."
                )
                await asyncio.sleep(wait)
                continue

        except Exception as e:
            last_exception = e
            # Server 5xx errors → retry
            if "server error" in str(e).lower() and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF ** attempt
                logger.warning(
                    f"LLM server error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {wait:.1f}s..."
                )
                await asyncio.sleep(wait)
                continue
            # Client 4xx errors → ne retry-uj
            raise

    # Sve pokušaje smo iscrpli
    raise Exception(f"LLM failed after {MAX_RETRIES + 1} attempts. Last error: {last_exception}")