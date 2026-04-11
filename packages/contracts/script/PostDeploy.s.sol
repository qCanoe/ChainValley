// SPDX-License-Identifier: MIT
pragma solidity >=0.8.24;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { StoreSwitch } from "@latticexyz/store/src/StoreSwitch.sol";

import { IWorld } from "../src/codegen/world/IWorld.sol";

contract PostDeploy is Script {
  function run(address worldAddress) external {
    StoreSwitch.setStoreAddress(worldAddress);

    uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

    vm.startBroadcast(deployerPrivateKey);

    uint256 doInit = vm.envOr("FISHERY_DO_INIT", uint256(0));
    if (doInit == 1) {
      uint256 hard = vm.envOr("FISHERY_HARD_RULE", uint256(1));
      uint32 stock = IWorld(worldAddress).app__initFishery(hard == 1);
      console.log("Fishery init stock:", stock);
    }

    console.log("World deployed at:", worldAddress);

    vm.stopBroadcast();
  }
}
