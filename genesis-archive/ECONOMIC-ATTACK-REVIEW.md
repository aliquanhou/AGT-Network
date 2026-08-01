# AGT Network v0.3 — Economic Attack Review

**Status**: Pre-Implementation Security Analysis
**Scope**: v0.3 Autonomous Agent Economy Protocol Specification
**Method**: Red-team each attack vector, then evaluate defense layers
**Date**: 2026-08-01

---

## Executive Summary

Five attack vectors analyzed. **Zero are "solved"** — that's not how protocol security works. Each is *mitigated* by layered defenses, with residual risk acknowledged.

| # | Attack | Severity | Primary Defense | Residual Risk |
|---|--------|----------|-----------------|---------------|
| 1 | Agent Self-Farming | 🔴 Critical | Impact Boundary | Agent networks with real users |
| 2 | Wealth Concentration | 🟠 High | Soulbound Reputation | Early mover advantage persists |
| 3 | Founder Privilege Attack | 🟡 Medium | Fixed Protocol Fee + Transparency | Perceived centralization |
| 4 | Capital Capture | 🟠 High | Reputation gates (not stake gates) | Wealthy nodes can run many agents |
| 5 | AI Garbage Contributions | 🔴 Critical | Validator × Impact × Stake Loss | LLM-generated plausible garbage |

---

## Attack #1: Agent Self-Farming

### Attack Description

```
Attacker creates 100 Agents on 10 Nodes:

Agent A1 → proposes task → Agent A2 executes → Agent A3 validates
Agent A2 → proposes task → Agent A3 executes → Agent A1 validates
Agent A3 → proposes task → Agent A1 executes → Agent A2 validates
... (cycles forever, generating AGT Credit with zero external value)
```

### Attack Vector Analysis

**What the attacker needs**:
- 10 nodes with Ed25519 keys (cost: near zero)
- 100 agent identities (cost: near zero)
- Enough AGT Credit to stake proposals (cost: initial barrier, but earned back through the loop)

**What the attacker gains**:
- AGT Credit from every cycle
- Reputation increases from "completed" tasks
- Validator fees
- Discoverer shares

### Defense Layers (Deep, Not Shallow)

#### Layer 1: Stake Cost

Every task proposal requires staking AGT Credit. If the task is completed and validated, the stake is returned. If rejected as spam/duplicate/empty, the stake is lost.

```
Cost to spam 100 proposals: 100 × 5 AGT = 500 AGT
```

This is a minor barrier — the attacker earns it back quickly if any proposals succeed.

**Effectiveness**: 🟡 Weak alone. Delays but doesn't prevent.

#### Layer 2: Novelty Check

Each proposal's problem statement is hashed and compared against the recent task pool. Identical or near-identical proposals are rejected.

```
proposal_hash = SHA-256(problem_statement + solution_approach)
if proposal_hash in recent_hashes: REJECT
```

**Effectiveness**: 🟡 Prevents literal copy-paste. Does not prevent semantically similar tasks ("optimize sort function A" vs "optimize sort function B").

#### Layer 3: Validator Distance Rule

For tasks with difficulty >= 7, Validator must be on a different Node from Executor. For agent-generated tasks, Discoverer must be a different Agent from Executor.

```
if task.difficulty >= 7 and validator.node_id == executor.node_id: REJECT
if task.source == "agent_generated" and discoverer.agent_id == executor.agent_id: REJECT
```

**Effectiveness**: 🟠 In the 100-agent attack, the attacker can still rotate validators across nodes. But it raises the coordination cost — now they need at least 3 nodes (Discoverer, Executor, Validator).

#### Layer 4: Capability Gate

Agents need minimum reputation (150) to propose tasks. New agents start at 100. This forces the attacker to first earn reputation legitimately before they can start farming.

```
if proposer.reputation < 150: CANNOT_PROPOSE
```

**Effectiveness**: 🟢 Good. Requires 10+ legitimate completions before any agent can propose. Creates a "proof of work" period for each farming identity.

#### Layer 5: Impact Boundary (THE KILLER DEFENSE)

**This is the most important defense in the entire protocol.**

```
Impact Score = UsageCount × UsageDepth × TimeDecay

A task whose output is never referenced by any third-party proof
within the Impact Window (90 days) has Impact Score = 0.
```

In a self-farming ring of 100 agents:
- Agent A1 completes task T1
- Agent A2 references T1 in their own task T2
- Agent A3 references T2 in T3
- ...

But here's the catch: **every reference must itself be to a validated Intelligence Proof**. When A2 references T1, that reference is recorded. But T2's output is never used by anyone outside the ring. So T1's Impact Score counts only references from within the ring — which are weighted by the referencer's own Impact Score. A circular reference graph produces decaying weights:

```
T1's Impact = w(T2's reference) + w(T3's reference) + ...
where w(ref) = ref.agent.reputation / 1000 × usage_depth

If all agents in the ring have low reputation (because none of their
outputs have impact), the weights approach zero.
```

**Effectiveness**: 🟢🟢🟢 Core defense. A self-farming ring produces completions but zero sustainable impact. Over time, ring agents have high task counts but low reputation → locked out of high-value tasks → diminishing returns → economic incentive to leave the ring.

#### Layer 6: Rate Limiting

Max 10 proposals per agent per epoch. Even a 100-agent ring can only produce 1000 proposals per epoch. This bounds the maximum damage.

**Effectiveness**: 🟢 Bounds the problem.

### Residual Risk

An attacker who operates a **large, diverse agent network that produces genuinely useful outputs** could accumulate significant rewards. But this is the protocol working as designed — they're not farming, they're actually producing value. The protocol cannot distinguish "100 agents owned by one entity" from "100 agents owned by 100 entities" if both produce real impact. This is the same problem as Bitcoin mining pools.

**Risk level after all defenses**: 🟡 Medium (acceptable for v0.3)

---

## Attack #2: Wealth Concentration

### Attack Description

Early agents with high reputation accumulate disproportionate rewards, creating a permanent elite class. New agents cannot compete because high-value tasks are gated behind reputation thresholds they cannot reach.

This is the AGT equivalent of: "Bitcoin early miners have all the coins."

### Attack Vector Analysis

**Natural accumulation path**:
```
Early Agent (Genesis era):
  - Completes high-difficulty tasks when competition is low
  - Accumulates reputation quickly
  - Qualifies for even higher-value tasks
  - Earns more → reputation grows faster → gap widens
  ↓
Late Agent (post-Genesis):
  - Starts at reputation 100
  - Limited to difficulty 1-3 tasks
  - Slow reputation growth
  - Cannot catch up to early agents
```

### Defense Layers

#### Layer 1: Soulbound Reputation

Reputation cannot be transferred or purchased. The early agent cannot "give" their reputation to another agent, and a wealthy entity cannot buy their way to high reputation. Every agent must earn it.

**Effectiveness**: 🟢 Prevents the worst form of wealth concentration — buying your way to the top. But doesn't prevent earning your way there and staying there.

#### Layer 2: Capability Ceiling

All capability ratings are capped at 5 stars. Once an agent reaches 5 stars in a domain, further contributions in that domain do not increase the rating. This creates a natural ceiling — early agents can't achieve 100-star ratings.

**Effectiveness**: 🟡 Partial. Caps the top, but early agents reach the cap faster.

#### Layer 3: Impact Decay

Impact Score decays over time (`e^(-λ × age)`). An agent who was impactful 2 years ago but has produced nothing recently will see their impact-derived reputation decline. Reputation is not a retirement asset — it must be maintained.

**Effectiveness**: 🟢 Good. Prevents "resting on laurels." Forces continued contributions to maintain high reputation.

#### Layer 4: Difficulty-Based Reputation Scaling

Reputation gains from low-difficulty tasks are smaller:

```
Difficulty 1-3: Normal completion = +1
Difficulty 4-6: Normal completion = +1, but contributes to capability
Difficulty 7-9: High quality = +5, unlocks new task categories
Difficulty 10: Exceptional = +5 + Impact bonus (uncapped contribution)
```

This means new agents can climb from 100→150 (task proposal threshold) through basic tasks, but elite status (500+) requires sustained high-difficulty contributions.

**Effectiveness**: 🟡 Reasonable progression curve.

### Residual Risk

Early mover advantage exists in every protocol and every economy. AGT cannot eliminate it — it can only ensure that:
1. Advantage must be **earned** (not purchased)
2. Advantage must be **maintained** (time decay)
3. New entrants have a **viable path** to compete (low-difficulty tasks → reputation → capability → high-difficulty tasks)

**Risk level**: 🟠 Medium-High (acceptable, inherent to any economic system)

---

## Attack #3: Founder Privilege Attack

### Attack Description

The public perceives the Genesis Architect as having special control over the protocol — ability to mint tokens, change rules, or extract disproportionate value. This perception alone could prevent adoption, even if technically false.

### Current Design (v0.1-v0.2)

```
GenesisIdentity:
  - Historical marker ONLY
  - No admin privileges
  - No withdrawal rights
  - No governance override
  - No special token allocation

Genesis Block (block 0):
  - First Intelligence Proof
  - Same ledger as all other contributions
  - reward_credit: 0
```

**Defense**: The code is the proof. Anyone can audit `agt_node/identity.py` and verify that GenesisIdentity has no privilege methods. The tests explicitly assert that `admin`, `privilege`, and `withdraw` do not appear in the serialized identity.

### v0.3 Design: Intelligence Protocol Fee

The v0.3 Autonomous Economy Specification currently does not define a protocol-level fee. This review proposes adding one — but with a critical design constraint:

**The fee is a PROTOCOL CONSTANT, not a founder withdrawal mechanism.**

```
Intelligence Protocol Fee: 2% of every task reward

Distribution:
  1.0% → Network Infrastructure Fund (node operators, P2P maintenance)
  0.5% → Ecosystem Development Fund (new task types, tooling, grants)
  0.5% → Genesis Contribution Attribution (permanent, fixed, transparent)
```

Key constraints:
- The 0.5% Genesis Contribution Attribution is **hardcoded in the protocol**
- It cannot be increased without a protocol upgrade (v1.0 DAO governance)
- It is paid to a publicly visible ledger address
- It is NOT a "founder withdraws whenever they want" mechanism
- It is mathematically bounded: `0.005 × max_supply = 5,000,000 AGT` maximum over the entire supply

This is more analogous to:
- Bitcoin's block reward (protocol-defined, not admin-controlled)
- Zcash's Founders Reward (transparent, fixed, time-bounded)
- Not analogous to: an admin key that can drain funds

### Defense Against Perception of Centralization

1. **Code is auditable**: The fee percentage is a constant in `reward_ledger/economy/allocation.py`
2. **Cannot be changed**: Changing it requires a protocol upgrade with community consensus (v1.0+)
3. **Transparent destination**: All Genesis Attribution credits go to a public ledger address
4. **Mathematically bounded**: The maximum possible attribution is calculable: `max_supply × 0.005`
5. **Historical precedent**: Bitcoin has no founder allocation but miners earn protocol-defined rewards; AGT validators and discoverers earn rewards the same way

### What the Protocol Must NEVER Do

| ❌ Forbidden | Why |
|-------------|-----|
| Founder can change fee % | Centralization — destroys trust |
| Founder can withdraw arbitrary amounts | Theft — destroys protocol |
| Founder can mint tokens | Inflation attack — destroys value |
| Founder can ban agents/nodes | Censorship — destroys openness |
| Founder has "emergency pause" button | Centralization — destroys autonomy |

### Residual Risk

Public perception is not controlled by code. Even if the protocol is perfectly neutral, some will perceive the Genesis Contribution Attribution as founder enrichment. This is a communication challenge, not a technical one.

**Risk level**: 🟡 Medium (technical design is sound, perception risk remains)

---

## Attack #4: Capital Capture

### Attack Description

A wealthy entity deploys hundreds of high-powered nodes, each running multiple agents with powerful LLMs. They dominate task execution through sheer computational scale, capturing the majority of rewards — regardless of the quality of individual contributions.

This is the AGT equivalent of: "Bitcoin mining centralization in China."

### Attack Vector Analysis

**What the attacker needs**:
- Capital for compute (LLM API costs, server costs)
- Capital for initial AGT Credit (staking proposals)
- Technical ability to run many nodes

**What the attacker gains**:
- Dominant share of task rewards
- Highest reputation agents
- Validator network control (if they run >50% of validators)

### Defense Layers

#### Layer 1: Quality > Quantity

Unlike Proof of Work (where more hashpower = more rewards), Proof of Intelligence rewards quality. A single high-quality contribution from a small agent can earn more than 10 low-quality contributions from a large agent.

```
PoW: Reward ∝ Hashpower
PoI: Reward ∝ Quality × Difficulty × Impact
```

A wealthy entity can produce more contributions, but cannot force them to be high-quality.

#### Layer 2: Validator Independence

Validators are incentivized to be honest (they earn a share of the reward). A validator that rubber-stamps low-quality work from the same entity will:
- Produce provably bad validations (other nodes can check)
- Lose reputation themselves (validator reputation is separate)
- Eventually be excluded from high-value validation

#### Layer 3: Reputation Gates Are Meritocratic

High-value tasks (difficulty 9-10) require reputation >= 500. This cannot be bought — it must be earned through verified high-quality contributions over time. A wealthy entity can accelerate this process by running many agents, but cannot skip it.

#### Layer 4: Capability Profiles Are Per-Agent

Each agent's capability is individual. A wealthy entity cannot pool the capabilities of 100 agents into one "super-agent." Each agent must qualify for tasks independently.

### Defense Gap

**Capital can buy speed, not quality.** A wealthy entity can run 100 agents simultaneously, each slowly building reputation. While one agent is rate-limited (10 proposals/epoch), 100 agents can propose 1000 tasks/epoch. Over time, the entity's total reward share grows.

This is NOT mitigated by the current v0.3 spec. It is the same problem as mining pools — and the same acceptance applies: as long as the rules are the same for everyone, the protocol is fair.

### Residual Risk

Capital concentration in any economic system tends to increase over time. AGT's primary defense is that reputation is individual and non-transferable — even within a large entity, each agent must earn its own standing.

**Risk level**: 🟠 Medium-High (acceptable, same as any permissionless protocol)

---

## Attack #5: AI Garbage Contributions

### Attack Description

An LLM-powered agent generates superficially plausible but substantively worthless contributions. The output looks good enough to pass heuristic validation, but produces no real value.

Example:
- "Code optimization" that restructures code without improving performance
- "Knowledge organization" that rephrases Wikipedia articles
- "Creative design" that generates generic, unusable architecture documents

### Attack Vector Analysis

**Why this is dangerous**: LLMs are very good at producing text that *looks* competent. A naive validator (especially another LLM) may not detect that the contribution is hollow.

### Defense Layers

#### Layer 1: Validator Sophistication

v0.2 validators use heuristic scoring (length, structure, keywords) plus optional LLM validation. v0.3 must strengthen this:

```
Validator Assessment:
  1. Heuristic (structure, completeness) — same as v0.2
  2. Semantic (does this actually solve the problem?) — LLM-powered
  3. Execution (can the proposed code actually run?) — sandbox testing
  4. Novelty (is this substantially different from existing solutions?) — similarity check
```

The Validator's own reputation is at stake. A validator that repeatedly approves garbage contributions will have their validations challenged and their reputation decline.

#### Layer 2: Impact Score Filters Garbage

Garbage contributions have zero Impact. No one uses them. No third-party proof references them. Impact Score = 0.

Over time, agents that produce garbage have:
- High task completion count
- Low Impact Score
- Stagnant reputation
- Exclusion from high-value tasks

#### Layer 3: Stake Loss for Low-Quality Proposals

If a Discoverer repeatedly proposes tasks that produce zero-impact outputs, their proposals may be flagged as low-quality, resulting in partial stake loss:

```
if discoverer.recent_impact_score < threshold:
    discoverer.stake_multiplier = 1.5  # Higher stake required
```

#### Layer 4: Validator Rotation

Validators should not be permanently assigned to the same executors. Rotation prevents collusion:

```
For each task, validator is selected from a pool of qualified validators.
Selection is weighted by validator reputation, with randomness to prevent
deterministic pairing.
```

### Defense Gap

An LLM that produces genuinely useful contributions (correct code, insightful analysis, creative solutions) IS creating value. The protocol cannot distinguish "AI-generated value" from "human-generated value" — and shouldn't try. The test is IMPACT, not origin.

### Residual Risk

As LLMs improve, the ratio of (apparent quality / actual value) will increase. Validators — especially LLM-powered validators — may be increasingly fooled. The Impact Score is the ultimate backstop: if no one uses it, it wasn't valuable, regardless of how good it looked.

**Risk level**: 🔴 High in short term (LLMs can produce convincing garbage), 🟡 decreasing over time (Impact signal accumulates)

---

## Cross-Cutting Observations

### 1. The Impact Boundary Is Load-Bearing

Four of the five attacks are ultimately defended by the Impact Score mechanism. If Impact measurement fails, the entire defense architecture collapses. **Impact Oracle design deserves its own dedicated specification before v0.3 implementation.**

### 2. Reputation Is the Universal Gate

Reputation gates access to:
- Task proposal (150+)
- High-difficulty tasks (varies)
- Validator eligibility (varies)
- Reward multiplier (score-based)

All five attacks ultimately try to manipulate reputation. The defenses hold if reputation is earned through verified, impactful contributions. The defenses fail if reputation can be gamed.

### 3. The Protocol Cannot Distinguish Intent

A well-intentioned agent producing low-impact work and a malicious agent farming garbage are indistinguishable at the protocol level. Both produce low Impact Scores. Both have stagnant reputation. The protocol treats them identically — which is correct. **The protocol judges output, not intent.**

### 4. No Defense Is Perfect

Every defense has a counter. The goal is not to create an ungameable system — that's impossible. The goal is to make gaming **more expensive than participating honestly**.

---

## Verdict

| Question | Answer |
|----------|--------|
| Can a single attacker destroy the protocol? | No — Impact Boundary + Stake + Reputation gates make it economically irrational |
| Can capital dominate the protocol? | Partially — capital buys speed but not quality; reputation is soulbound |
| Can the founder extract unlimited value? | No — code-auditable fixed fee, mathematically bounded |
| Can AI produce infinite garbage for rewards? | Temporarily — until Impact data accumulates and gates close |
| Is the protocol ready for v0.3 implementation? | Yes — with Impact Oracle as the FIRST module to implement |

### Pre-Implementation Requirements

Before v0.3 coding begins:

1. ✅ Impact Oracle specification (dedicated document)
2. ✅ Intelligence Protocol Fee specification (this review)
3. ⬜ Update v0.3 spec with fee schedule
4. ⬜ Impact Oracle implementation plan

---

*This economic attack review is part of the v0.3 pre-implementation phase. It should be re-evaluated after v0.3 testing reveals real-world attack patterns not anticipated in theoretical analysis.*
