// SPDX-License-Identifier: MIT
pragma solidity >=0.8.24;

import { System } from "@latticexyz/world/src/System.sol";
import { FisheryPool, FisheryPoolData } from "../codegen/index.sol";
import { Inventory } from "../codegen/index.sol";
import { RoundLog, RoundLogData } from "../codegen/index.sol";

contract FisherySystem is System {
  uint8 public constant QUOTA_PER_AGENT = 4;
  uint32 public constant INITIAL_STOCK = 100;
  uint32 public constant COLLAPSE_THRESHOLD = 10;
  uint8 public constant AGENT_COUNT = 5;

  event ViolationAttempt(bytes32 indexed agentId, uint8 requested, uint8 accepted);
  event RoundClosed(uint32 indexed round, uint32 stockAfterHarvest, uint32 stockAfterRegeneration, bool collapsed);

  mapping(bytes32 agentId => uint32 requestedHarvest) private _pendingHarvests;
  mapping(bytes32 agentId => bool submitted) private _submittedThisRound;
  uint8 private _submissionCount;

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

  /// @notice Record a single agent's requested harvest for the current round.
  function harvest(bytes32 agentId, uint8 requested) public returns (uint8 accepted) {
    FisheryPoolData memory pool = FisheryPool.get();
    require(pool.stock > 0 || pool.round > 0, "Not initialized");
    require(!pool.collapsed, "Fishery collapsed");
    require(_isKnownAgent(agentId), "Unknown agent");
    require(!_submittedThisRound[agentId], "Agent already submitted");

    if (pool.hardRule) {
      require(requested <= QUOTA_PER_AGENT, "Exceeds quota");
      accepted = requested;
    } else {
      accepted = requested;
      if (requested > QUOTA_PER_AGENT) {
        emit ViolationAttempt(agentId, requested, accepted);
      }
    }
    _pendingHarvests[agentId] = uint32(accepted);
    _submittedThisRound[agentId] = true;
    _submissionCount += 1;

    return accepted;
  }

  /// @notice Record a failed hard-rule attempt as a zero-settlement submission so the round can still close.
  function recordRejectedHarvest(bytes32 agentId, uint8 requested) public {
    FisheryPoolData memory pool = FisheryPool.get();
    require(pool.stock > 0 || pool.round > 0, "Not initialized");
    require(!pool.collapsed, "Fishery collapsed");
    require(pool.hardRule, "Only hard rule");
    require(requested > QUOTA_PER_AGENT, "Not a quota violation");
    require(_isKnownAgent(agentId), "Unknown agent");
    require(!_submittedThisRound[agentId], "Agent already submitted");

    emit ViolationAttempt(agentId, requested, 0);
    _pendingHarvests[agentId] = 0;
    _submittedThisRound[agentId] = true;
    _submissionCount += 1;
  }

  /// @notice Finalize a round after all 5 agents have submitted harvests.
  function endRound() public returns (uint32 round, uint32 stockAfterRegeneration, bool collapsed) {
    FisheryPoolData memory pool = FisheryPool.get();
    require(pool.stock > 0 || pool.round > 0, "Not initialized");
    require(!pool.collapsed, "Fishery collapsed");
    require(_submissionCount == AGENT_COUNT, "Round incomplete");

    round = pool.round + 1;

    uint32 totalRequested = 0;
    uint32[5] memory requested;
    uint32[5] memory executed;
    uint32[5] memory remainders;

    for (uint8 i = 0; i < AGENT_COUNT; i++) {
      requested[i] = _pendingHarvests[_agentIdAt(i)];
      totalRequested += requested[i];
    }

    uint32 available = pool.stock;
    uint32 allocated = 0;
    if (totalRequested <= available) {
      for (uint8 i = 0; i < AGENT_COUNT; i++) {
        executed[i] = requested[i];
        allocated += executed[i];
      }
    } else if (totalRequested > 0) {
      for (uint8 i = 0; i < AGENT_COUNT; i++) {
        uint32 numerator = requested[i] * available;
        executed[i] = numerator / totalRequested;
        remainders[i] = numerator % totalRequested;
        allocated += executed[i];
      }

      uint32 leftover = available - allocated;
      while (leftover > 0) {
        uint8 best = 0;
        for (uint8 i = 1; i < AGENT_COUNT; i++) {
          if (remainders[i] > remainders[best]) {
            best = i;
          }
        }
        executed[best] += 1;
        remainders[best] = 0;
        leftover -= 1;
      }
    }

    uint32 stockAfterHarvest = available;
    for (uint8 i = 0; i < AGENT_COUNT; i++) {
      bytes32 agentId = _agentIdAt(i);
      stockAfterHarvest -= executed[i];
      uint32 prev = Inventory.get(agentId);
      Inventory.set(agentId, prev + executed[i]);
    }

    RoundLogData memory logData = RoundLogData({
      harvest0: executed[0],
      harvest1: executed[1],
      harvest2: executed[2],
      harvest3: executed[3],
      harvest4: executed[4]
    });
    RoundLog.set(round, logData);

    stockAfterRegeneration = stockAfterHarvest + (stockAfterHarvest / 10);
    collapsed = stockAfterRegeneration < COLLAPSE_THRESHOLD;

    FisheryPool.set(
      FisheryPoolData({
        stock: stockAfterRegeneration,
        round: round,
        collapsed: collapsed,
        hardRule: pool.hardRule
      })
    );

    emit RoundClosed(round, stockAfterHarvest, stockAfterRegeneration, collapsed);
    _clearRoundState();
  }

  /// @notice Read singleton pool state (for RPC / off-chain orchestrator).
  function getPoolState()
    public
    view
    returns (uint32 stock, uint32 round, bool collapsed, bool hardRule)
  {
    FisheryPoolData memory pool = FisheryPool.get();
    return (pool.stock, pool.round, pool.collapsed, pool.hardRule);
  }

  /// @notice Expose current round submissions so off-chain orchestration can recover after interruption.
  function getPendingRoundState()
    public
    view
    returns (uint8 submissionCount, bool[5] memory submitted, uint32[5] memory requestedHarvests)
  {
    submissionCount = _submissionCount;
    for (uint8 i = 0; i < AGENT_COUNT; i++) {
      submitted[i] = _submittedThisRound[_agentIdAt(i)];
      requestedHarvests[i] = _pendingHarvests[_agentIdAt(i)];
    }
  }

  function getRoundLog(uint32 round) public view returns (uint32[5] memory executedHarvests) {
    RoundLogData memory logData = RoundLog.get(round);
    executedHarvests[0] = logData.harvest0;
    executedHarvests[1] = logData.harvest1;
    executedHarvests[2] = logData.harvest2;
    executedHarvests[3] = logData.harvest3;
    executedHarvests[4] = logData.harvest4;
  }

  function getAllCumulativeHarvests() public view returns (uint32[5] memory cumulativeHarvests) {
    for (uint8 i = 0; i < AGENT_COUNT; i++) {
      cumulativeHarvests[i] = Inventory.get(_agentIdAt(i));
    }
  }

  function _clearRoundState() internal {
    for (uint8 i = 0; i < AGENT_COUNT; i++) {
      bytes32 agentId = _agentIdAt(i);
      delete _pendingHarvests[agentId];
      delete _submittedThisRound[agentId];
    }
    _submissionCount = 0;
  }

  function _isKnownAgent(bytes32 agentId) internal pure returns (bool) {
    return agentId == _agentIdAt(0) ||
      agentId == _agentIdAt(1) ||
      agentId == _agentIdAt(2) ||
      agentId == _agentIdAt(3) ||
      agentId == _agentIdAt(4);
  }

  function _agentIdAt(uint8 index) internal pure returns (bytes32) {
    return bytes32(uint256(index + 1));
  }
}
