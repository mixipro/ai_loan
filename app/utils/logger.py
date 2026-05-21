# app/utils/logger.py

import json
from pathlib import Path
from datetime import datetime


LOG_FILE = Path("logs/llm_logs.jsonl")

# automatski napravi folder
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_llm_interaction(
    agent: str,
    prompt: str,
    raw_response: str,
    parsed_response=None,
    success: bool = True,
    error: str = None
):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent,
        "prompt": prompt,
        "raw_response": raw_response,
        "parsed_response": parsed_response,
        "success": success,
        "error": error
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")