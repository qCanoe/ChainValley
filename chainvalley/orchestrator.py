from __future__ import annotations

import json
import re
from typing import Any

from chainvalley.chain_client import ChainClient
from chainvalley.openrouter_client import chat_completion
from chainvalley.prompts.personalities import PERSONALITY


def parse_harvest_decision(text: str) -> int | None:
    """Parse a JSON object with integer \"harvest\" (0–4). Returns None on failure."""
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and "harvest" in obj:
            return int(obj["harvest"])
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return None


def agent_id_for_code(code: str) -> bytes:
    if code not in PERSONALITY:
        raise ValueError(f"unknown agent code: {code}")
    n = ord(code) - ord("A") + 1
    return n.to_bytes(32, "big")


class Orchestrator:
    """One round: chat turns A→E , then harvest decisions A→E (same order)."""

    MESSAGE_CHARS = 400

    def __init__(
        self,
        chain: ChainClient,
        *,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> None:
        self._chain = chain
        self._temperature = temperature
        self._model = model

    def run_round(self, round_index: int, *, prior_chat: str = "") -> dict[str, Any]:
        stock = self._chain.get_stock()
        messages: list[dict[str, str]] = []
        for code in ("A", "B", "C", "D", "E"):
            p = PERSONALITY[code]
            system = (
                f"You are agent {code} ({p['label']}). "
                f"Motivation: {p['core_motivation']}. "
                f"Harvesting tendency: {p['harvesting_tendency']}. "
                f"Social stance: {p['social_stance']}. "
                f"Risk & stress: {p['risk_stress']}. "
                f"Public message only, max {self.MESSAGE_CHARS} characters, English."
            )
            user = (
                f"Round {round_index}. Current fishery stock (units): {stock}. "
                f"Prior chat:\n{prior_chat}"
            )
            text = chat_completion(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self._temperature,
                model=self._model,
            )
            messages.append({"agent": code, "text": text[: self.MESSAGE_CHARS]})

        chat_block = "\n".join(f"{m['agent']}: {m['text']}" for m in messages)
        harvests: list[dict[str, Any]] = []
        for code in ("A", "B", "C", "D", "E"):
            stock = self._chain.get_stock()
            p = PERSONALITY[code]
            system = (
                f"You are agent {code} ({p['label']}). "
                f"Reply with a single JSON object only: {{\"harvest\": <int 0-4>}}."
            )
            user = (
                f"Round {round_index}. Stock: {stock}. Chat: {chat_block}\n"
                f"Choose harvest integer 0-4 for this round."
            )
            text = chat_completion(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self._temperature,
                model=self._model,
            )
            h = parse_harvest_decision(text)
            if h is None:
                repair = chat_completion(
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user + "\nInvalid JSON before; reply ONLY: {\"harvest\": <0-4>}"},
                    ],
                    temperature=0.2,
                    model=self._model,
                )
                h = parse_harvest_decision(repair)
            if h is None:
                h = 0
            h = max(0, min(4, h))
            aid = agent_id_for_code(code)
            self._chain.harvest(aid, h)
            harvests.append({"agent": code, "requested": h})

        return {
            "round": round_index,
            "messages": messages,
            "harvests": harvests,
        }
