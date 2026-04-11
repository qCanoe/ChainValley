from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Resolve .env from project root (parent of `chainvalley/`), not the current working directory.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_PROJECT_ROOT / ".env")


DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# OpenRouter deprecated `qwen/qwen3.6-plus:free` (404); use paid route below.
DEFAULT_OPENROUTER_MODEL = "qwen/qwen3.6-plus"


@dataclass(frozen=True)
class OpenRouterSettings:
    api_key: str
    base_url: str
    model: str
    http_referer: str | None
    app_title: str | None


def get_openrouter_settings() -> OpenRouterSettings:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing. Copy .env.example to .env and set your key."
        )
    return OpenRouterSettings(
        api_key=key,
        base_url=os.environ.get("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL).rstrip("/"),
        model=os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip(),
        http_referer=(os.environ.get("OPENROUTER_HTTP_REFERER") or "").strip() or None,
        app_title=(os.environ.get("OPENROUTER_APP_TITLE") or "").strip() or None,
    )
