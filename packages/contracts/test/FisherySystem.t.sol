// SPDX-License-Identifier: MIT
pragma solidity >=0.8.24;

import "forge-std/Test.sol";
import { MudTest } from "@latticexyz/world/test/MudTest.t.sol";

import { IWorld } from "../src/codegen/world/IWorld.sol";
import { Inventory } from "../src/codegen/index.sol";
import { FisheryPool } from "../src/codegen/index.sol";

contract FisherySystemTest is MudTest {
  event ViolationAttempt(bytes32 indexed agentId, uint8 requested, uint8 executed);

  bytes32 internal constant AGENT = bytes32(uint256(1));

  function test_hardRule_revertsWhenHarvestExceedsQuota() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);
    vm.expectRevert();
    w.app__harvest(AGENT, 5);
  }

  function test_softRule_acceptsOverQuotaAndRecordsAttempt() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(false);
    vm.expectEmit(true, true, true, true);
    emit ViolationAttempt(AGENT, 5, 5);
    uint8 executed = w.app__harvest(AGENT, 5);
    assertEq(executed, 5);
    assertEq(Inventory.get(AGENT), 5);
    assertEq(FisheryPool.getStock(), 95);
  }

  function test_hardRule_allowsHarvestWithinQuota() public {
    IWorld w = IWorld(worldAddress);
    w.app__initFishery(true);
    uint8 executed = w.app__harvest(AGENT, 4);
    assertEq(executed, 4);
    assertEq(Inventory.get(AGENT), 4);
    assertEq(FisheryPool.getStock(), 96);
  }
}
