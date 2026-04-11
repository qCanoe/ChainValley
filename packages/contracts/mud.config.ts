import { defineWorld } from "@latticexyz/world";

export default defineWorld({
  namespace: "app",
  tables: {
    Counter: {
      schema: {
        value: "uint32",
      },
      key: [],
    },
    FisheryPool: {
      schema: {
        stock: "uint32",
        round: "uint32",
        collapsed: "bool",
      },
      key: [],
    },
    AgentProfile: {
      schema: {
        agentId: "bytes32",
        personalityCode: "uint8",
      },
      key: ["agentId"],
    },
    Inventory: {
      schema: {
        agentId: "bytes32",
        cumulativeHarvest: "uint32",
      },
      key: ["agentId"],
    },
    RoundLog: {
      schema: {
        round: "uint32",
        harvest0: "uint32",
        harvest1: "uint32",
        harvest2: "uint32",
        harvest3: "uint32",
        harvest4: "uint32",
      },
      key: ["round"],
    },
  },
});
