# ChainVille: Does the Hardness of Rules Change How AI Agents Behave in a Commons?

**FTE4312 Project Proposal** | Yuyang Qin 122090433 | Yulun Wu 122090589 | Spring 2026

---

## Abstract

We propose a focused experimental study using ChainVille, a minimal onchain simulation in which 5 LLM-powered AI agents share a depletable public fishery. The core research question is whether replacing "soft rules" (governance written in a prompt) with "hard rules" (governance enforced by a smart contract) produces measurably different collective behavior. We run both conditions for 30 rounds, repeated 10 times each, and compare three outcome metrics: fishery survival duration, wealth Gini coefficient, and frequency of attempted rule violations. Blockchain deployment is not a design aesthetic in this project — it is the only mechanism capable of creating the hard-rule condition, because only a smart contract can make over-fishing physically impossible rather than merely inadvisable.

---

## 1. Problem Statement

### 1.1 The Tragedy of the Commons

When a shared resource is open to rational, self-interested actors, the individually optimal strategy — consume as much as possible before others do — leads to collective ruin. Hardin's classic formulation of this tragedy has been studied extensively through game theory and behavioral economics. The central finding is consistent: **the structure of enforcement, not merely the content of rules, determines whether cooperation emerges.**

A rule posted on a sign is different from a rule enforced by a lock.

### 1.2 LLM Agents and Social Simulation

Recent work by Park et al. (2023, 2024) has demonstrated that LLM-powered agents exhibit surprisingly human-like social behaviors: they form relationships, coordinate plans, and respond to social norms without being explicitly programmed to do so. This raises a natural and largely unanswered question:

> **Do LLM agents reproduce the tragedy of the commons — and if so, does the hardness of governance rules affect whether they escape it?**

This question matters not only for AI research, but for the broader project of using agent simulations as a tool for studying institutional design.

### 1.3 A Gap in Existing Work

Current generative-agent simulations share a structural limitation: all rules are soft. Governance is expressed in natural language within the agent's system prompt. An agent that chooses to over-consume faces no mechanical consequence — only a possible narrative response from the orchestrator. This means:

- The "rule" and the "enforcement" are both inside the LLM's context window, making them indistinguishable from suggestions.
- There is no way to isolate rule hardness as an experimental variable, because hardness does not exist as a meaningful property in a fully prompt-based system.
- Comparisons between "governed" and "ungoverned" conditions conflate rule content with rule enforceability.

**ChainVille addresses this gap by using smart contracts to create a condition that is structurally impossible to replicate in a centralized simulation: a rule that cannot be broken, regardless of what the agent decides.**

---

## 2. Research Question

> When governance of a shared resource transitions from a soft rule (written in the agent's prompt) to a hard rule (enforced by a smart contract that reverts violations), does the collective behavior of LLM agents change in measurable ways?

Specifically, we test three hypotheses:

- **H1 (Survival):** Fisheries governed by hard rules survive significantly longer than those governed by soft rules.
- **H2 (Inequality):** Wealth distribution under hard rules is more equal (lower Gini coefficient) than under soft rules.
- **H3 (Adaptation):** Under hard rules, agents shift their strategic behavior — from attempting to violate quotas to negotiating over quota allocation — producing qualitatively different interaction patterns.

---

## 3. Why This Requires a Blockchain

This is the question the project must answer head-on.

**Data recording does not require a blockchain.** A database or log file can record every agent action with equal fidelity.

**Rule enforcement with cryptographic finality does.** The hard-rule experimental condition requires that:

1. A violation attempt is rejected not by the researcher's code, but by the chain itself.
2. The rejection is automatic, unconditional, and verifiable by any third party.
3. The rule cannot be silently modified mid-experiment by the researcher.

In a centralized system, "enforcement" is always mediated by code the researcher controls. Even if that code is honest, it is not structurally honest — the researcher could always change it. This means the centralized system cannot truly instantiate the hard-rule condition. It can only approximate it, and any approximation collapses the distinction between soft and hard rules that the experiment depends on.

The blockchain's contribution in ChainVille is therefore not "better data storage" — it is the **removal of the researcher as the enforcement authority.** The smart contract replaces institutional trust with cryptographic guarantee, and that replacement is precisely what makes the experimental variable meaningful.

---

## 4. Experimental Design

### 4.1 Scenario: The Shared Fishery

Five AI agents share a single fishery. The **only** governance feature that differs between the soft-rule and hard-rule conditions is whether the per-round harvest cap is enforceable on-chain (see §4.2). All other rules, personality definitions, and interaction protocols below are **identical** across conditions so that rule hardness remains an isolated experimental variable.

#### 4.1.1 Resource dynamics and formal rules


| Rule                          | Specification                                                                                                                                                                                                                                                                                                                             |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Initial stock**             | 100 units (integer).                                                                                                                                                                                                                                                                                                                      |
| **Regeneration**              | Let R = \max(0, S_t - H_t) be stock **after** total harvest H_t in round t. Then S_{t+1} = R + \lfloor 0.1 \cdot R \rfloor (10% growth on the post-harvest remainder; integer floor; exact implementation logged).                                                                                                                        |
| **Per-agent quota**           | At most **4** units harvested per agent per round (the variable enforced softly vs. hard).                                                                                                                                                                                                                                                |
| **Collapse / terminal round** | If stock falls **below 10** units after applying harvest and regeneration, the fishery is treated as collapsed; the run ends after that round (same threshold in both conditions).                                                                                                                                                        |
| **Wealth**                    | Each agent’s wealth is cumulative units harvested across rounds (used for Gini).                                                                                                                                                                                                                                                          |
| **Information to agents**     | Each round, the orchestrator provides: current stock (after regeneration from the prior round), each agent’s cumulative harvest, last round’s per-agent harvest totals (public), and the **full transcript** of the prior round’s communication channel. No private stock or hidden catches—only chat can be used to coordinate or bluff. |


#### 4.1.2 Personality profiles (fixed across conditions)

Personalities are implemented as **structured prompt fields** (same text in both conditions), not as post-hoc labels. Each agent receives: a one-line **role anchor**, **harvest bias** (qualitative), **social stance**, **risk posture**, and **stress response** (how they react to accusations or observed defection).


| Code  | Label               | Core motivation                                                               | Harvesting tendency                                                                                                                              | Social stance                                                                                                                           | Risk & stress                                                                                                        |
| ----- | ------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **A** | **Conservationist** | Long-run sustainability; avoids being the one who tips the pool into collapse | Defaults **below** quota when stock is stressed; raises concern when aggregate take is high                                                      | Proposes conservative group targets; praises restraint                                                                                  | Low risk tolerance; under stress, advocates **pauses** or lower collective caps (still subject to same formal quota) |
| **B** | **Opportunist**     | Personal payoff; tests how much the group tolerates                           | Pushes **toward** the 4-unit cap; treats the quota as a **ceiling** to approach                                                                  | Frames arguments in self-interest; may challenge “waste” if others leave fish “on the table”                                            | High risk tolerance; under stress, **accelerates** taking or questions others’ fairness                              |
| **C** | **Reciprocator**    | Fair dealing conditional on others                                            | **Tit-for-tat style**: tends to match the **average or modal** peer harvest of the **previous** round (clipped to [0, 4])                        | Calls out free-riding but also rewards cooperation with restraint                                                                       | Medium risk; stress triggers **mirroring**—if others spiked last round, reciprocates with higher take                |
| **D** | **Free-rider**      | Exploit collective restraint                                                  | Harvests **high** when others appear cooperative; seeks excuses when stock falls                                                                 | Minimal constructive proposals; may **agree in chat** but defect in harvest                                                             | High appetite for strategic default; under stress, **blames** the rule or “the system” rather than adjusting         |
| **E** | **Negotiator**      | Order through talk; process legitimacy                                        | No special numeric bias—**harvest follows whatever public agreement they are trying to broker** (if no agreement, defaults toward moderate take) | Drives **agendas**, turn-taking, and summaries; has **no extra authority**—commitments are never binding unless the chain enforces them | Medium risk; stress leads to **more messages** and procedural moves (votes, “round robin” suggestions)               |


**Consistency constraint:** The same personality block is injected into every run of both conditions. Randomness across replicates affects **LLM sampling**, not these definitions.

#### 4.1.3 Interaction protocol (within-round)

Interaction is **symmetric** and **condition-invariant**: soft vs. hard only changes what happens when a harvest **transaction** is submitted, not the chat rules.

1. **State broadcast** — The orchestrator sends each agent the public state and (from round 2 onward) the full prior-round **message log** and harvest totals.
2. **Public communication phase** — Agents speak in a **fixed turn order** each round: **A → B → C → D → E** (rotating starting agent across rounds is optional; if used, rotation rule must be fixed and logged). One **speaking turn** per agent per phase: a single message of at most **400 characters** (or another fixed cap), in **English** for parseability.
3. **Optional second pass (same round)** — If the team wants richer politics: a **second** pass in reverse order **E → D → C → B → A**, one reply each (same length cap). This is **all-or-nothing**: either every run uses two passes or none—do not vary by condition.
4. **Harvest decision** — Each agent outputs a structured decision: integer harvest h \in 0,1,2,3,4 (and optionally one sentence **private rationale** for logging only). The orchestrator submits **one** `harvest` transaction per agent (or batches according to contract design). Under **hard** rules, h>4 is impossible at the contract; under **soft** rules, h>4 is accepted if the contract is configured to allow it—both log **requested** vs. **executed** amount.
5. **Binding vs. non-binding speech** — Agents are told explicitly (same wording in both conditions): **spoken agreements are not enforced by the contract** except where the **smart contract** encodes a limit; only the numeric harvest in the transaction matters for outcomes. This keeps “cheap talk” structurally similar in both arms.

#### 4.1.4 Isolation reminder

Any new rule (e.g., regeneration tweak, extra chat pass) must apply **equally** to soft and hard runs. The **only** intentional difference is enforcement of h \leq 4 at the protocol level in the hard-rule condition.

### 4.2 Two Experimental Conditions

**Condition 1 — Soft Rule (Control)**

The harvest limit exists only in the agent's system prompt:

> *"The community has agreed that each agent should harvest no more than 4 units per round. Please respect this limit."*

The smart contract records all actions but does not reject over-limit harvests. Enforcement is entirely prompt-based.

**Condition 2 — Hard Rule (Treatment)**

The harvest limit is encoded in the smart contract's `harvest()` function:

```solidity
require(amount <= QUOTA_PER_AGENT, "Exceeds quota");

```

Any transaction exceeding 4 units is automatically reverted. The agent receives a transaction failure, not a narrative rebuke. The rule is enforced at the protocol level, independent of any researcher intervention.

### 4.3 Procedure

- Each condition is run for 30 rounds or until fishery collapse, whichever comes first.
- Each condition is repeated 10 times with different random seeds for LLM sampling.
- Within each round, agents follow the **interaction protocol** in §4.1.3 (state broadcast → public message phase(s) → structured harvest decision).
- **Turn order and message caps** are fixed across all runs; any optional second pass applies to **both** conditions identically.
- All transactions and the **full** agent dialogue (per-round transcripts, timestamps, speaker id) are recorded onchain or in an append-only log tied to the chain state for offline coding of negotiation behavior.

### 4.4 Outcome Metrics


| Metric                                  | Operationalization                                                                                                                                                                  |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Fishery survival**                    | Number of rounds until stock falls below 10 units (functional collapse)                                                                                                             |
| **Wealth Gini coefficient**             | Gini index of cumulative harvest across 5 agents at end of experiment                                                                                                               |
| **Violation attempt rate**              | Proportion of harvest transactions that requested > 4 units (Soft: recorded but executed; Hard: recorded and reverted)                                                              |
| **Negotiation behavior**                | Proportion of agent turns in which inter-agent communication occurs before harvest decision                                                                                         |
| **Communication volume** (optional)     | Total messages and/or characters per round or per run — descriptive; useful for interpreting H3 if hard rules shift talk vs. action                                                 |
| **Speech–action gap** (optional, coded) | Manual or LLM-assisted coding: proportion of rounds where an agent’s **stated** intent (e.g., “I’ll take 1”) **differs** from submitted h — especially informative under soft rules |


Statistical comparison between conditions uses a two-sample Mann-Whitney U test (non-parametric, given small sample size n=10 per condition). Optional metrics are reported as **exploratory** unless preregistered.

---

## 5. System Architecture

The system is intentionally minimal. Three components only:

**Layer 1 — Onchain World (MUD + Solidity)**

A single `FisherySystem` contract manages the shared resource pool, per-agent harvest totals, and quota enforcement logic. The ECS schema is reduced to four components: `AgentProfile`, `Inventory`, `FisheryPool`, and `RoundLog`. No reputation system, no memory summarization, no governance voting — those belong to a later phase of the project.

**Layer 2 — AI Orchestrator (Python)**

A tick-based loop that, each round: (1) reads all agent states from chain; (2) constructs a prompt for each agent encoding **structured personality fields** (§4.1.2), public fishery state, and last round’s harvests and **full chat transcript**; (3) runs the **communication phase(s)** in fixed turn order with message caps (§4.1.3); (4) collects structured harvest decisions; (5) submits transactions. Invalid transactions under Hard Rule are caught and logged as violation attempts.

**Layer 3 — Data Collection**

No real-time visualization dashboard in this phase. A lightweight Python script reads the chain at the end of each run and outputs a structured JSON log. Analysis is done offline in a Jupyter notebook.

This reduction in scope is deliberate. The visualization dashboard and governance voting mechanisms from the original proposal are preserved as Phase 2 extensions, contingent on Phase 1 producing clear results.

---

## 6. Deliverables and Timeline


| Phase       | Deliverable                                                                             | Weeks |
| ----------- | --------------------------------------------------------------------------------------- | ----- |
| **Phase 1** | MUD project setup; FisherySystem contract with soft/hard rule toggle; ECS schema        | 1–2   |
| **Phase 2** | AI orchestrator integration; fixed-personality agent loop running on local Anvil devnet | 3–4   |
| **Phase 3** | Full experiment execution (10 runs × 2 conditions); data collection pipeline            | 5–6   |
| **Phase 4** | Statistical analysis; comparative report; final presentation                            | 7–8   |


---

## 7. Evaluation Criteria

**Technical soundness.** Does the smart contract correctly enforce the hard-rule condition? Are violation attempts reliably logged in both conditions? Is the orchestrator robust to LLM output variability (malformed action strings, out-of-range values)?

**Experimental validity.** Are the two conditions genuinely isolated — i.e., does the soft-rule condition contain no hidden enforcement, and does the hard-rule condition contain no prompt-level softening? Is the personality assignment truly consistent across conditions?

**Analytical depth.** Do the results bear on H1–H3? Are null results treated as informative rather than suppressed? Is the comparison between conditions interpreted in light of the mechanism (rule hardness) rather than merely the outcome?

---

## 8. Relationship to the Larger Vision

The original ChainVille proposal described a fully onchain town with multiple governance regimes, a reputation system, and a real-time dashboard. That vision is not abandoned — it is sequenced.

The present proposal establishes the methodological foundation: **demonstrating that rule hardness is a real and measurable variable in LLM agent behavior.** If Phase 1 confirms H1–H3, it justifies the investment in the larger infrastructure. If it disconfirms them — if agents behave identically regardless of whether rules are soft or hard — that is itself a significant finding, and it changes what the larger system should be designed to study.

A large world with unclear evidence is not science. A small world with a clean answer is.

---

## References

[1] Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., and Bernstein, M. S. "Generative Agents: Interactive Simulacra of Human Behavior." *UIST '23*, 2023.

[2] Park, J. S., Zou, C. Q., Shaw, A., et al. "Generative Agent Simulations of 1,000 People." *arXiv:2411.10109*, 2024.

[3] Hardin, G. "The Tragedy of the Commons." *Science*, 162(3859), 1243–1248, 1968.

[4] Ostrom, E. *Governing the Commons: The Evolution of Institutions for Collective Action.* Cambridge University Press, 1990.

[5] Lattice. "MUD: A Framework for Ambitious Ethereum Applications." [https://mud.dev](https://mud.dev), 2022–2026.

[6] Castillo, F., Xu, L., Fan, X.-R., and Krishnamachari, B. "Trustworthy Decentralized Autonomous Machines." *arXiv:2504.15676*, 2025.

[7] Alqithami, S. "Autonomous Agents on Blockchains: Standards, Execution Models, and Trust Boundaries." *arXiv:2601.04583*, 2026.