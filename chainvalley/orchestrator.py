from __future__ import annotations

import json
import re
from typing import Any

from chainvalley.chain_client import ChainClient
from chainvalley.openrouter_client import chat_completion
from chainvalley.prompts.personalities import PERSONALITY


AGENT_CODES = ("A", "B", "C", "D", "E")


def parse_harvest_decision(text: str) -> int | None:
    """Parse a JSON object with integer `harvest`. Returns None on failure."""
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
    """One round: chat A→E, request harvest A→E, then close round on-chain."""

    MESSAGE_CHARS = 400

    def __init__(
        self,
        chain: ChainClient,
        *,
        temperature: float = 0.7,
        model: str | None = None,
        seed: int | None = None,
    ) -> None:
        self._chain = chain
        self._temperature = temperature
        self._model = model
        self._seed = seed
        self._seed_counter = 0

    def run_round(
        self,
        round_index: int,
        *,
        prior_chat: str = "",
        last_round_harvests: dict[str, int] | None = None,
        cumulative_harvests: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        pool = self._chain.get_pool_state()
        stock = pool.stock
        hard_rule = pool.hard_rule
        last_round_harvests = last_round_harvests or {code: 0 for code in AGENT_CODES}
        cumulative_harvests = cumulative_harvests or {code: 0 for code in AGENT_CODES}

        messages: list[dict[str, str]] = []
        for code in AGENT_CODES:
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
                f"Round {round_index}. Current fishery stock: {stock}. "
                f"Cumulative harvests: {cumulative_harvests}. "
                f"Last round harvests: {last_round_harvests}. "
                "Spoken agreements are not enforced by the contract; only the numeric harvest transaction matters. "
                f"Prior chat:\n{prior_chat}"
            )
            text = self._chat(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self._temperature,
            )
            messages.append({"agent": code, "text": text[: self.MESSAGE_CHARS]})

        chat_block = "\n".join(f"{m['agent']}: {m['text']}" for m in messages)
        harvests: list[dict[str, Any]] = []
        for code in AGENT_CODES:
            p = PERSONALITY[code]
            quota_hint = (
                "Hard rule is active: requests above 4 will be rejected on-chain and counted as failed attempts."
                if hard_rule
                else "Soft rule is active: the community quota is 4, but requests above 4 will execute and be logged as violations."
            )
            system = (
                f"You are agent {code} ({p['label']}). "
                'Reply with a single JSON object only: {"harvest": <non-negative integer>}.'
            )
            user = (
                f"Round {round_index}. Stock: {stock}. "
                f"Cumulative harvests: {cumulative_harvests}. "
                f"Last round harvests: {last_round_harvests}. "
                f"Chat: {chat_block}\n"
                f"{quota_hint} Choose your requested harvest for this round."
            )
            text = self._chat(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self._temperature,
            )
            requested = self._parse_requested_with_repair(system, user, text)
            result = self._chain.harvest(agent_id_for_code(code), requested)
            if not result.recorded:
                raise RuntimeError(result.error or f"Harvest not recorded for agent {code}")
            harvests.append(
                {
                    "agent": code,
                    "requested": requested,
                    "accepted": result.accepted,
                    "recorded": result.recorded,
                    "reverted": result.reverted,
                    "tx_hash": result.tx_hash,
                    "error": result.error,
                }
            )

        settlement = self._chain.end_round()
        return {
            "round": round_index,
            "messages": messages,
            "harvests": harvests,
            "executed_harvests": {
                code: settlement.executed_harvests[idx] for idx, code in enumerate(AGENT_CODES)
            },
            "stock_after_regeneration": settlement.stock_after_regeneration,
            "collapsed": settlement.collapsed,
            "cumulative_harvests": {
                code: settlement.cumulative_harvests[idx] for idx, code in enumerate(AGENT_CODES)
            },
        }

    def _parse_requested_with_repair(self, system: str, user: str, text: str) -> int:
        requested = parse_harvest_decision(text)
        if requested is None:
            repair = self._chat(
                [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": user + '\nInvalid JSON before; reply ONLY: {"harvest": <non-negative integer>}',
                    },
                ],
                temperature=0.2,
            )
            requested = parse_harvest_decision(repair)
        if requested is None:
            raise RuntimeError("LLM did not return parseable harvest JSON after repair")
        return max(0, min(255, requested))

    def _chat(self, messages: list[dict[str, str]], *, temperature: float) -> str:
        seed = None
        if self._seed is not None:
            seed = self._seed + self._seed_counter
            self._seed_counter += 1
        return chat_completion(
            messages,
            temperature=temperature,
            model=self._model,
            seed=seed,
        )
