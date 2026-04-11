from __future__ import annotations

import json
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

    def get_pool_state(self) -> tuple[int, int, bool, bool]:
        fn = self._contract.functions.app__getPoolState()
        stock, rnd, collapsed, hard = fn.call()
        return int(stock), int(rnd), bool(collapsed), bool(hard)

    def get_stock(self) -> int:
        stock, _, _, _ = self.get_pool_state()
        return stock

    def init_fishery(self, hard_rule: bool) -> int:
        if self._account is None:
            raise RuntimeError("init_fishery requires private_key")
        fn = self._contract.functions.app__initFishery(hard_rule)
        tx = self._build_and_send(fn)
        rc = self._w3.eth.wait_for_transaction_receipt(tx)
        if rc["status"] != 1:
            raise RuntimeError("initFishery transaction failed")
        return self.get_stock()

    def harvest(self, agent_id: str | bytes, requested: int) -> int:
        if self._account is None:
            raise RuntimeError("harvest requires private_key")
        aid = _to_bytes32(agent_id)
        fn = self._contract.functions.app__harvest(aid, int(requested))
        tx = self._build_and_send(fn)
        rc = self._w3.eth.wait_for_transaction_receipt(tx)
        if rc["status"] != 1:
            raise RuntimeError("harvest transaction failed")
        return int(requested)

    def _build_and_send(self, fn: Any) -> bytes:
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
        return self._w3.eth.send_raw_transaction(raw)
