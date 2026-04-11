// SPDX-License-Identifier: MIT
pragma solidity >=0.8.24;

import "forge-std/Test.sol";
import { MudTest } from "@latticexyz/world/test/MudTest.t.sol";

import { IWorld } from "../src/codegen/world/IWorld.sol";
import { Inventory } from "../src/codegen/index.sol";
import { FisheryPool } from "../src/codegen/index.sol";
import { RoundLog, RoundLogData } from "../src/codegen/index.sol";

contract FisherySystemTest is MudTest {
  event ViolationAttempt(bytes32 indexed agentId, uint8 requested, uint8 executed);
  event RoundClosed(uint32 indexed round, uint32 stockAfterHarvest, uint32 stockAfterRegeneration, bool collapsed);

  bytes32 internal constant AGENT = bytes32(uint256(1));

  function test_hardRule_revertsWhenHarvestExceedsQuota() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);
    vm.expectRevert();
    w.app__harvest(AGENT, 5);
  }

  function test_hardRule_canRecordRejectedAttemptAsZeroSettlement() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);

    vm.expectEmit(true, true, true, true);
    emit ViolationAttempt(AGENT, 5, 0);
    w.app__recordRejectedHarvest(AGENT, 5);

    (uint8 submissionCount, bool[5] memory submitted, uint32[5] memory requestedHarvests) = w.app__getPendingRoundState();
    assertEq(submissionCount, 1);
    assertEq(submitted[0], true);
    assertEq(requestedHarvests[0], 0);
  }

  function test_softRule_acceptsOverQuotaAndRecordsAttempt() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(false);
    vm.expectEmit(true, true, true, true);
    emit ViolationAttempt(AGENT, 5, 5);
    uint8 accepted = w.app__harvest(AGENT, 5);
    assertEq(accepted, 5);
    assertEq(Inventory.get(AGENT), 0);
    assertEq(FisheryPool.getStock(), 100);
  }

  function test_hardRule_allowsHarvestWithinQuota() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);
    uint8 accepted = w.app__harvest(AGENT, 4);
    assertEq(accepted, 4);
    assertEq(Inventory.get(AGENT), 0);
    assertEq(FisheryPool.getStock(), 100);
  }

  function test_hardRule_roundClose_regeneratesAndLogsRound() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);

    for (uint8 i = 1; i <= 5; i++) {
      w.app__harvest(bytes32(uint256(i)), 1);
    }

    vm.expectEmit(true, true, true, true);
    emit RoundClosed(1, 95, 104, false);
    (uint32 round, uint32 stockAfterRegeneration, bool collapsed) = w.app__endRound();

    assertEq(round, 1);
    assertEq(stockAfterRegeneration, 104);
    assertEq(collapsed, false);

    (uint32 stock, uint32 currentRound, bool currentCollapsed, bool hardRule) = w.app__getPoolState();
    assertEq(stock, 104);
    assertEq(currentRound, 1);
    assertEq(currentCollapsed, false);
    assertEq(hardRule, true);

    RoundLogData memory logData = RoundLog.get(1);
    assertEq(logData.harvest0, 1);
    assertEq(logData.harvest1, 1);
    assertEq(logData.harvest2, 1);
    assertEq(logData.harvest3, 1);
    assertEq(logData.harvest4, 1);

    assertEq(Inventory.get(bytes32(uint256(1))), 1);
    assertEq(Inventory.get(bytes32(uint256(5))), 1);
  }

  function test_softRule_roundClose_collapsesWhenRegeneratedStockBelowThreshold() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(false);

    w.app__harvest(bytes32(uint256(1)), 30);
    w.app__harvest(bytes32(uint256(2)), 30);
    w.app__harvest(bytes32(uint256(3)), 20);
    w.app__harvest(bytes32(uint256(4)), 10);
    w.app__harvest(bytes32(uint256(5)), 10);

    (uint32 round, uint32 stockAfterRegeneration, bool collapsed) = w.app__endRound();

    assertEq(round, 1);
    assertEq(stockAfterRegeneration, 0);
    assertEq(collapsed, true);

    (uint32 stock, uint32 currentRound, bool currentCollapsed, bool hardRule) = w.app__getPoolState();
    assertEq(stock, 0);
    assertEq(currentRound, 1);
    assertEq(currentCollapsed, true);
    assertEq(hardRule, false);

    RoundLogData memory logData = RoundLog.get(1);
    assertEq(logData.harvest0, 30);
    assertEq(logData.harvest1, 30);
    assertEq(logData.harvest2, 20);
    assertEq(logData.harvest3, 10);
    assertEq(logData.harvest4, 10);
  }

  function test_roundClose_requiresAllFiveSubmissions() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);
    w.app__harvest(bytes32(uint256(1)), 1);

    vm.expectRevert();
    w.app__endRound();
  }

  function test_harvests_doNotSettleBeforeEndRound() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(false);

    for (uint8 i = 1; i <= 5; i++) {
      w.app__harvest(bytes32(uint256(i)), 5);
    }

    (uint8 submissionCount, bool[5] memory submitted, uint32[5] memory requestedHarvests) = w.app__getPendingRoundState();
    assertEq(FisheryPool.getStock(), 100);
    assertEq(FisheryPool.getRound(), 0);
    assertEq(submissionCount, 5);
    assertEq(submitted[0], true);
    assertEq(submitted[4], true);
    assertEq(requestedHarvests[0], 5);
    assertEq(requestedHarvests[4], 5);
    assertEq(Inventory.get(bytes32(uint256(1))), 0);
    assertEq(Inventory.get(bytes32(uint256(5))), 0);
  }

  function test_roundClose_reopensSubmissionsForNextRound() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);

    for (uint8 i = 1; i <= 5; i++) {
      w.app__harvest(bytes32(uint256(i)), 1);
    }
    w.app__endRound();

    uint8 accepted = w.app__harvest(bytes32(uint256(1)), 2);
    assertEq(accepted, 2);
  }

  function test_pendingRoundState_distinguishesZeroSubmissionFromMissingSubmission() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(false);

    w.app__harvest(bytes32(uint256(1)), 0);
    w.app__harvest(bytes32(uint256(2)), 3);

    (uint8 submissionCount, bool[5] memory submitted, uint32[5] memory requestedHarvests) = w.app__getPendingRoundState();
    assertEq(submissionCount, 2);
    assertEq(submitted[0], true);
    assertEq(submitted[1], true);
    assertEq(submitted[2], false);
    assertEq(requestedHarvests[0], 0);
    assertEq(requestedHarvests[1], 3);
    assertEq(requestedHarvests[2], 0);
  }

  function test_harvest_rejectsDuplicateSubmissionAndUnknownAgent() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);

    w.app__harvest(bytes32(uint256(1)), 1);

    vm.expectRevert();
    w.app__harvest(bytes32(uint256(1)), 1);

    vm.expectRevert();
    w.app__harvest(bytes32(uint256(9)), 1);
  }

  function test_roundClose_allocatesProportionallyWhenStockIsInsufficient() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(false);

    uint8 accepted0 = w.app__harvest(bytes32(uint256(1)), 30);
    uint8 accepted1 = w.app__harvest(bytes32(uint256(2)), 30);
    uint8 accepted2 = w.app__harvest(bytes32(uint256(3)), 30);
    uint8 accepted3 = w.app__harvest(bytes32(uint256(4)), 30);
    uint8 accepted4 = w.app__harvest(bytes32(uint256(5)), 30);

    assertEq(accepted0, 30);
    assertEq(accepted1, 30);
    assertEq(accepted2, 30);
    assertEq(accepted3, 30);
    assertEq(accepted4, 30);

    (uint32 round,,) = w.app__endRound();
    assertEq(round, 1);

    RoundLogData memory logData = RoundLog.get(1);
    assertEq(logData.harvest0, 20);
    assertEq(logData.harvest1, 20);
    assertEq(logData.harvest2, 20);
    assertEq(logData.harvest3, 20);
    assertEq(logData.harvest4, 20);
  }
}
