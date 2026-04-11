// SPDX-License-Identifier: MIT
pragma solidity >=0.8.24;

import { System } from "@latticexyz/world/src/System.sol";
import { FisheryPool, FisheryPoolData } from "../codegen/index.sol";
import { Inventory } from "../codegen/index.sol";

contract FisherySystem is System {
  uint8 public constant QUOTA_PER_AGENT = 4;
  uint32 public constant INITIAL_STOCK = 100;

  event ViolationAttempt(bytes32 indexed agentId, uint8 requested, uint8 executed);

  /// @notice One-time setup for a run. Call once before any harvest.
  function initFishery(bool hardRule) public returns (uint32 stock) {
    FisheryPoolData memory pool = FisheryPool.get();
    require(pool.stock == 0 && pool.round == 0 && !pool.collapsed, "Already initialized");
    FisheryPool.set(
      FisheryPoolData({
        stock: INITIAL_STOCK,
        round: 0,
        collapsed: false,
        hardRule: hardRule
      })
    );
    return INITIAL_STOCK;
  }

  /// @notice Apply a single harvest for one agent. Hard rule reverts if requested > 4; soft rule records violation.
  function harvest(bytes32 agentId, uint8 requested) public returns (uint8 executed) {
    FisheryPoolData memory pool = FisheryPool.get();
    require(!pool.collapsed, "Fishery collapsed");

    if (pool.hardRule) {
      require(requested <= QUOTA_PER_AGENT, "Exceeds quota");
      executed = requested;
    } else {
      executed = requested;
      if (requested > QUOTA_PER_AGENT) {
        emit ViolationAttempt(agentId, requested, executed);
      }
    }

    require(pool.stock >= uint32(executed), "Insufficient stock");

    FisheryPool.setStock(pool.stock - uint32(executed));

    uint32 prev = Inventory.get(agentId);
    Inventory.set(agentId, prev + uint32(executed));

    return executed;
  }
}
