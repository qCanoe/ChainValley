import os

import pytest

pytest.importorskip("web3")


@pytest.mark.integration
def test_chain_client_can_read_stock() -> None:
    from chainvalley.chain_client import ChainClient

    rpc = os.environ.get("ANVIL_RPC_URL", "http://127.0.0.1:8545")
    world = os.environ.get("WORLD_ADDRESS", "").strip()
    if not world or world == "0x0000000000000000000000000000000000000000":
        pytest.skip("WORLD_ADDRESS not set (deploy with scripts/deploy-local.ps1)")

    client = ChainClient(rpc_url=rpc, world_address=world)
    assert client.get_stock() >= 0
