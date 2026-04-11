from __future__ import annotations

from typing import Any

from openai import OpenAI

from chainvalley.config import get_openrouter_settings


def create_openrouter_client() -> OpenAI:
    s = get_openrouter_settings()
    headers: dict[str, str] = {}
    if s.http_referer:
        headers["HTTP-Referer"] = s.http_referer
    if s.app_title:
        headers["X-Title"] = s.app_title
    return OpenAI(
        base_url=s.base_url,
        api_key=s.api_key,
        default_headers=headers or None,
    )


def chat_completion(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = 1024,
    seed: int | None = None,
) -> str:
    """
    Single non-streaming chat completion. Returns assistant text content.
    """
    client = create_openrouter_client()
    s = get_openrouter_settings()
    use_model = model if model is not None else s.model
    kwargs: dict[str, Any] = {
        "model": use_model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if seed is not None:
        kwargs["seed"] = seed
    resp = client.chat.completions.create(**kwargs)
    choice = resp.choices[0]
    content = choice.message.content
    if content is None:
        return ""
    return content.strip()
