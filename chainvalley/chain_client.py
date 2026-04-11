from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eth_account import Account
from web3 import Web3
from web3.contract import Contract


def _load_abi() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parent / "abi" / "world.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _to_bytes32(agent_id: str | bytes) -> bytes:
    if isinstance(agent_id, bytes):
        if len(agent_id) != 32:
            raise ValueError("agent_id bytes must be length 32")
        return agent_id
    if agent_id.startswith("0x") and len(agent_id) == 66:
        return bytes.fromhex(agent_id[2:])
    text = agent_id.encode("utf-8")
    if len(text) > 32:
        return Web3.keccak(text=text)
    return text.ljust(32, b"\0")


@dataclass(frozen=True)
class PoolState:
    stock: int
    round: int
    collapsed: bool
    hard_rule: bool


@dataclass(frozen=True)
class PendingRoundState:
    submission_count: int
    submitted: list[bool]
    requested_harvests: list[int]


@dataclass(frozen=True)
class HarvestSubmissionResult:
    agent_id_hex: str
    requested: int
    accepted: int
    recorded: bool
    reverted: bool
    tx_hash: str | None
    error: str | None


@dataclass(frozen=True)
class RoundSettlement:
    round: int
    stock_after_regeneration: int
    collapsed: bool
    executed_harvests: list[int]
    cumulative_harvests: list[int]
    tx_hash: str


class ChainClient:
    """Thin RPC wrapper around the MUD World contract (FisherySystem methods)."""

    def __init__(
        self,
        rpc_url: str,
        world_address: str,
        *,
        private_key: str | None = None,
        chain_id: int | None = None,
    ) -> None:
        self._w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self._w3.is_connected():
            raise RuntimeError(f"Cannot connect to RPC: {rpc_url}")
        self._world_address = Web3.to_checksum_address(world_address)
        self._abi = _load_abi()
        self._contract: Contract = self._w3.eth.contract(
            address=self._world_address, abi=self._abi
        )
        self._account: Account | None = None
        self._chain_id = chain_id
        if private_key:
            self._account = Account.from_key(private_key)
            if self._chain_id is None:
                self._chain_id = int(self._w3.eth.chain_id)

    def get_pool_state(self) -> PoolState:
        fn = self._contract.functions.app__getPoolState()
        stock, rnd, collapsed, hard = fn.call()
        return PoolState(int(stock), int(rnd), bool(collapsed), bool(hard))

    def get_stock(self) -> int:
        return self.get_pool_state().stock

    def get_pending_round_state(self) -> PendingRoundState:
        fn = self._contract.functions.app__getPendingRoundState()
        submission_count, submitted, requested = fn.call()
        return PendingRoundState(
            submission_count=int(submission_count),
            submitted=[bool(v) for v in submitted],
            requested_harvests=[int(v) for v in requested],
        )

    def get_round_log(self, round_number: int) -> list[int]:
        fn = self._contract.functions.app__getRoundLog(int(round_number))
        return [int(v) for v in fn.call()]

    def get_all_cumulative_harvests(self) -> list[int]:
        fn = self._contract.functions.app__getAllCumulativeHarvests()
        return [int(v) for v in fn.call()]

    def init_fishery(self, hard_rule: bool) -> PoolState:
        if self._account is None:
            raise RuntimeError("init_fishery requires private_key")
        fn = self._contract.functions.app__initFishery(hard_rule)
        tx_hash, rc = self._transact(fn)
        if rc["status"] != 1:
            raise RuntimeError("initFishery transaction failed")
        _ = tx_hash
        return self.get_pool_state()

    def harvest(self, agent_id: str | bytes, requested: int) -> HarvestSubmissionResult:
        if self._account is None:
            raise RuntimeError("harvest requires private_key")
        requested = int(requested)
        if requested < 0 or requested > 255:
            raise ValueError("requested harvest must fit uint8")
        aid = _to_bytes32(agent_id)
        pool = self.get_pool_state()
        if pool.hard_rule and requested > 4:
            fallback = self._contract.functions.app__recordRejectedHarvest(aid, requested)
            tx_hash, rc = self._transact(fallback)
            if rc["status"] == 1:
                return HarvestSubmissionResult(
                    agent_id_hex="0x" + aid.hex(),
                    requested=requested,
                    accepted=0,
                    recorded=True,
                    reverted=True,
                    tx_hash=tx_hash,
                    error="hard rule rejects requested harvests above 4",
                )
            return HarvestSubmissionResult(
                agent_id_hex="0x" + aid.hex(),
                requested=requested,
                accepted=0,
                recorded=False,
                reverted=True,
                tx_hash=tx_hash,
                error="recordRejectedHarvest transaction failed",
            )
        try:
            fn = self._contract.functions.app__harvest(aid, requested)
            tx_hash, rc = self._transact(fn)
            if rc["status"] != 1:
                return HarvestSubmissionResult(
                    agent_id_hex="0x" + aid.hex(),
                    requested=requested,
                    accepted=0,
                    recorded=False,
                    reverted=True,
                    tx_hash=tx_hash,
                    error="harvest transaction failed",
                )
            return HarvestSubmissionResult(
                agent_id_hex="0x" + aid.hex(),
                requested=requested,
                accepted=requested,
                recorded=True,
                reverted=False,
                tx_hash=tx_hash,
                error=None,
            )
        except Exception as exc:
            return HarvestSubmissionResult(
                agent_id_hex="0x" + aid.hex(),
                requested=requested,
                accepted=0,
                recorded=False,
                reverted=True,
                tx_hash=None,
                error=str(exc),
            )

    def end_round(self) -> RoundSettlement:
        if self._account is None:
            raise RuntimeError("end_round requires private_key")
        fn = self._contract.functions.app__endRound()
        tx_hash, rc = self._transact(fn)
        if rc["status"] != 1:
            raise RuntimeError("endRound transaction failed")
        pool = self.get_pool_state()
        executed = self.get_round_log(pool.round)
        cumulative = self.get_all_cumulative_harvests()
        return RoundSettlement(
            round=pool.round,
            stock_after_regeneration=pool.stock,
            collapsed=pool.collapsed,
            executed_harvests=executed,
            cumulative_harvests=cumulative,
            tx_hash=tx_hash,
        )

    def _transact(self, fn: Any) -> tuple[str, Any]:
        assert self._account is not None
        assert self._chain_id is not None
        base: dict[str, Any] = {
            "from": self._account.address,
            "nonce": self._w3.eth.get_transaction_count(self._account.address),
            "chainId": self._chain_id,
            "gasPrice": self._w3.eth.gas_price,
        }
        tx = fn.build_transaction(base)
        tx["gas"] = int(self._w3.eth.estimate_gas(tx))
        signed = self._account.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = self._w3.eth.send_raw_transaction(raw)
        receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex(), receipt
