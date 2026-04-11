/*
 * System calls for the World contract (FisherySystem).
 */

import { ClientComponents } from "./createClientComponents";
import { SetupNetworkResult } from "./setupNetwork";

export type SystemCalls = ReturnType<typeof createSystemCalls>;

export function createSystemCalls(
  { worldContract, waitForTransaction }: SetupNetworkResult,
  _components: ClientComponents,
) {
  const initFishery = async (hardRule: boolean) => {
    const tx = await worldContract.write.app__initFishery([hardRule]);
    await waitForTransaction(tx);
  };

  const harvest = async (agentId: `0x${string}`, requested: number) => {
    const tx = await worldContract.write.app__harvest([agentId, requested]);
    await waitForTransaction(tx);
  };

  return {
    initFishery,
    harvest,
  };
}
