# ChainValley

**On-chain commons simulation for comparing soft vs. hard governance of LLM agents.**

ChainValley implements **ChainVille**, a minimal shared-fishery experiment: five LLM-powered agents compete for a depletable stock. The **only** intentional difference between conditions is whether the per-round harvest cap is **prompt-only (soft)** or **enforced by a smart contract (hard)**. Everything else—personalities, turn order, and logging—stays aligned so rule hardness stays an isolated variable.

> Full experimental specification, hypotheses, and citations: **[`Project Description.md`](./Project%20Description.md)** (course proposal, Spring 2026).

---

## Why a blockchain here

Recording actions does not require a chain; **cryptographic enforcement of the quota** does. In the hard-rule arm, over-quota harvests are rejected by the contract itself—verifiable and not silently changeable mid-run—so “hardness” is not merely a narrative layer in the orchestrator.

---

## Research question

When governance shifts from a **soft rule** (quota in the prompt) to a **hard rule** (quota in `FisherySystem`), does collective behavior change on:

| Hypothesis | Outcome (summary) |
|------------|-------------------|
| **H1** | Fishery survival (rounds until collapse) |
| **H2** | Wealth inequality (Gini on cumulative harvest) |
| **H3** | Strategy and talk—e.g. violation attempts, negotiation patterns |

Design details: 30 rounds or collapse, 10 replicates per condition, Mann–Whitney U for soft vs. hard comparisons (see [`Project Description.md`](./Project%20Description.md) §4).

---

## Architecture

| Layer | Role |
|-------|------|
| **On-chain (MUD + Solidity)** | `FisherySystem`: pool, per-agent inventory, round log, soft/hard mode; `harvest` records requests; `endRound` settles stock, regeneration, and collapse. |
| **Orchestrator (Python)** | Reads chain state, runs fixed-turn chat + structured harvest JSON, submits txs; handles recovery for partial rounds. |
| **Data** | Run artifacts under `artifacts/runs/`; offline analysis in `notebooks/analysis.ipynb`. |

---

## Repository layout

```text
packages/contracts/     # MUD world, FisherySystem, Forge tests
chainvalley/            # Python: ChainClient, Orchestrator, experiment runner
tests/                  # pytest (parsing, helpers)
notebooks/              # Jupyter analysis
scripts/                # deploy-local.ps1 / .sh for local Anvil
```

---

## Prerequisites

- **Node.js** ≥ 20, **pnpm** ≥ 9  
- **Foundry** (`forge`, `anvil`) for building and testing contracts  
- **Python** 3.11+

---

## Quick start (local)

1. **Install JS deps** (from repo root):

   ```bash
   pnpm install --ignore-scripts
   ```

2. **Python deps**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment** — copy and fill a `.env` with at least your OpenAI-compatible API settings and RPC/account variables your `ChainClient` expects (see `chainvalley/chain_client.py` usage in `experiment.py`).

4. **Chain** — start Anvil, then deploy the world (PowerShell example):

   ```powershell
   .\scripts\deploy-local.ps1 -RpcUrl "http://127.0.0.1:8545" -DoInit "1" -HardRule "1"
   ```

   Set `WORLD_ADDRESS` (and related keys) to match the deployed world before running Python.

5. **Contract build & tests** (requires `forge`):

   ```bash
   pnpm --filter contracts run build
   pnpm --filter contracts run test
   ```

6. **Python tests**:

   ```bash
   pytest tests/ -v
   ```

---

## Experiment runs

The experiment driver lives in `chainvalley/experiment.py`: it can initialize the fishery, loop rounds via `Orchestrator`, write JSON under `artifacts/runs/`, and optionally deploy a fresh world per run when configured. For batch design (seeds, soft/hard), follow the parameters documented in code and in **[`Project Description.md`](./Project%20Description.md) §4.3**.

---

## Analysis

Use `notebooks/analysis.ipynb` to load completed run JSON files, compute metrics (survival, Gini, violation rate), and compare conditions. Incomplete runs may be saved as `*.partial.json` and are excluded from the notebook’s default aggregation.

---

## Notes

> [!TIP]
> **Naming:** The repository is **ChainValley**; the study and proposal title use **ChainVille**—same experiment.

> [!NOTE]
> Phase-2 extensions (dashboard, richer governance) are out of scope for the current minimal stack; see [`Project Description.md`](./Project%20Description.md) §6 for the staged roadmap.

> [!WARNING]
> **Secrets:** Never commit `.env` or private keys. The default `.gitignore` excludes common artifact and env patterns.

---

## Acknowledgments

Built with [MUD](https://mud.dev) (Lattice) and Foundry. Course project context and full references are listed in **[`Project Description.md`](./Project%20Description.md)**.
