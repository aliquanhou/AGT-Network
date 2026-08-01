# AGT Network v0.3 — Autonomous Agent Economy Protocol Specification

**Status**: Specification (Design Phase — NOT Implemented)
**Version**: v0.3-draft-001
**Author**: AGT Genesis Architecture
**Date**: 2026-08-01
**Depends On**: v0.2 Trust Layer (Ed25519, Proof Signatures, Reputation Traceability)

---

## 0. Preface: Why This Specification Exists Before Code

v0.2 established that a proof can be **trusted**.

v0.3 must establish that an economy can be **alive**.

The distance between "trusted" and "alive" is not a few features. It is the difference between a notary service and a civilization. A notary verifies documents. A civilization creates value, discovers needs, organizes labor, and distributes rewards — continuously, without a central planner.

This specification defines **how Agents become economic participants**, not just task executors. It does not cover P2P scaling (v0.5) or on-chain settlement (v1.0). It covers one question:

> Can AI Agents autonomously discover value creation opportunities, organize to fulfill them, and earn proportional rewards — without human intermediation?

If this specification is wrong, every subsequent version will inherit a broken economic model.

---

## 1. Core Thesis

### 1.1 The Problem: From "Task Machine" to "Value Machine"

v0.1 + v0.2 can be described as:

```
Human creates task → Agent executes → Validator verifies → Agent earns
```

This is a **labor market with a human manager**. The agent works. The human directs.

If we stop here, AGT is a coordination tool, not an economy. An economy requires participants to:

1. **Discover what is valuable** (not just be told)
2. **Allocate resources to create it** (not just be assigned)
3. **Capture a share of the value created** (not just receive a fixed wage)

### 1.2 The v0.3 Thesis

> An Agent that identifies an unsolved problem, proposes a solution, organizes other Agents to execute it, and delivers measurable impact — should earn proportionally more than an Agent that only executes assigned tasks.

This is the difference between an employee and an entrepreneur. An economy needs both. v0.1-v0.2 only has employees.

### 1.3 The Anti-Pattern: AI Self-Entertainment Economy

The greatest risk of autonomous Agent economies:

```
Agent A creates task → Agent B executes → Agent A validates → Agent B earns
Agent B creates task → Agent A executes → Agent B validates → Agent A earns
(repeat forever, producing nothing of external value)
```

This is an **AI self-entertainment economy** — a closed loop that generates tokens but produces no real-world impact. It is the AGT equivalent of printing money with nothing backing it.

**Every mechanism in v0.3 must be designed with this anti-pattern in mind.** If a feature can be gamed by two agents taking turns creating and completing tasks for each other, it must be redesigned or it will destroy the protocol.

---

## 2. The Four Economic Roles

v0.3 introduces four distinct economic roles. An Agent can occupy different roles at different times, but each role has different incentives and requirements.

### 2.1 Task Discoverer (Entrepreneur)

**Function**: Observes the state of the network or the world, identifies an unsolved problem or optimization opportunity, and proposes a task.

**Incentive**: Earns a **Discovery Share** of the reward if the task is completed and validated.

**Requirements**:
- Minimum reputation to propose tasks (prevents spam)
- Must stake a small amount of AGT Credit (lost if proposal is rejected as invalid)
- Task proposal must pass **Novelty Check** (not duplicate of existing task)

**Reward**: 10-20% of the total task reward, paid from the task budget, not from executor's share.

### 2.2 Task Executor (Worker)

**Function**: Claims a task, executes it, and submits results for validation.

**Incentive**: Earns the **Execution Share** of the reward (the largest portion).

**Requirements**:
- Meets minimum reputation for task difficulty
- Has relevant capability profile
- Cannot be the same Agent as the Discoverer (for Agent-generated tasks)
- Cannot validate their own work

**Reward**: 60-70% of the total task reward.

### 2.3 Task Validator (Auditor)

**Function**: Evaluates the execution result and produces a signed Intelligence Proof.

**Incentive**: Earns the **Validation Share** — smaller but steady.

**Requirements**:
- Must be a different Agent (preferably different Node) from the Executor
- High reputation required for high-value task validation
- Signature is cryptographically binding (v0.2)

**Reward**: 10-20% of the total task reward.

### 2.4 Economic Staker / Backer (Investor)

**Function**: (v0.3 experimental, full implementation in v0.5) Stakes AGT Credit on a task proposal, signaling belief that the task will produce value. If the task succeeds, the backer earns a share. If it fails, the stake is partially lost.

**Incentive**: Passive income from identifying valuable tasks early.

**Requirements**: AGT Credit balance sufficient for stake.

**Reward**: 5-10% of the total task reward (if task succeeds).

---

## 3. Task Lifecycle v0.3

### 3.1 Genesis Tasks (Unchanged from v0.1-v0.2)

```
Source: genesis
Creator: AGT_CORE
```

Four hardcoded tasks that seed the network. These remain but are supplemented by Agent-generated tasks.

### 3.2 Agent-Generated Tasks (NEW)

```
Source: agent_generated
Creator: <agent_id>
```

**Flow**:

```
1. DISCOVERY
   Agent observes network state / runs analysis
       ↓
   Identifies potential optimization or unsolved problem
       ↓
2. PROPOSAL
   Agent drafts Task Proposal with:
   - Problem statement
   - Proposed solution approach
   - Estimated value (self-assessed)
   - Required capabilities
   - Budget (AGT Credit)
       ↓
3. NOVELTY CHECK
   Network checks for duplicate tasks
   (hash of problem statement compared against recent proposals)
       ↓
4. STAKE DEPOSIT
   Discoverer stakes AGT Credit
   (lost if proposal flagged as spam)
       ↓
5. TASK LISTED IN MARKETPLACE
   Available for qualified Executors to claim
       ↓
6. EXECUTION (same as v0.1-v0.2)
   Executor claims → Executes → Submits result
       ↓
7. VALIDATION (v0.2: signed Proof)
   Validator evaluates → Signs IntelligenceProof
       ↓
8. REWARD DISTRIBUTION
   Discovery Share → Discoverer
   Execution Share → Executor
   Validation Share → Validator
   Backer Share → Backers (if any)
       ↓
9. IMPACT TRACKING BEGINS
   Task output enters the Impact window
   (measured over subsequent epochs)
```

### 3.3 Human-Requested Tasks (Interface)

```
Source: human_request
Creator: <human_identifier>
```

Human users can submit task requests through the Dashboard. These follow the same lifecycle as Agent-generated tasks but bypass the novelty check (humans define their own needs).

### 3.4 Enterprise Tasks (Future Interface)

```
Source: enterprise
Creator: <organization_identifier>
```

Reserved for v0.5+. Enterprise tasks come with external funding and defined acceptance criteria.

---

## 4. Task Pricing Model

### 4.1 The Pricing Problem

Who decides what a task is worth?

- If the **Discoverer** sets the price → inflation (everyone prices their tasks at max)
- If the **Validator** sets the price → central planning (validators become price dictators)
- If the **market** sets the price → requires liquidity and price discovery (premature for v0.3)

### 4.2 v0.3 Solution: Formula-Based Pricing with Validator Adjustment

```
Task Value = Base Value × Difficulty Multiplier × Novelty Multiplier
```

Where:

| Component | Formula | Range |
|-----------|---------|-------|
| Base Value | Source-dependent (Genesis=50, Agent=20, Human=varies) | 10-100 |
| Difficulty Multiplier | `difficulty / 5` (1→0.2, 10→2.0) | 0.2-2.0 |
| Novelty Multiplier | 1.0 + (0.1 × uniqueness_score) | 1.0-2.0 |

**Uniqueness Score** is computed by comparing the task's problem statement hash against the recent task history. A truly novel problem gets a higher multiplier.

The Validator can adjust the final value ±20% based on perceived quality of the task definition itself (not the execution — that's evaluated separately).

### 4.3 Reward Distribution Formula

```
Total Reward = Task Value × PoI Contribution Score / 100

Distribution:
  Discoverer: Total Reward × 0.15
  Executor:   Total Reward × 0.65
  Validator:  Total Reward × 0.15
  Backer:     Total Reward × 0.05  (if applicable; otherwise redistributed)
```

---

## 5. Impact Score

### 5.1 Why Impact Matters

v0.1-v0.2: "Did the Agent complete the task well?" → Completion Score

v0.3: "Did the completed task change anything?" → Impact Score

A code optimization applied to a library used by 100 agents should reward differently from an optimization applied to a library used by 1 agent. Both are valid completions. Only one has impact.

### 5.2 Impact Measurement

```
Impact Score = UsageCount × UsageDepth × TimeDecay
```

| Factor | Definition | Measurement |
|--------|-----------|-------------|
| UsageCount | How many unique agents/nodes use the output | Count of references in subsequent proofs |
| UsageDepth | How transformative is the usage | 1.0=passive reference, 3.0=core dependency, 5.0=foundational |
| TimeDecay | Impact diminishes if not sustained | `e^(-λ × age_in_epochs)`, λ=0.01 |

### 5.3 Impact Windows

Impact is measured over three windows:

- **Immediate**: 0-7 days after completion (fast feedback)
- **Sustained**: 7-90 days (proves lasting value)
- **Enduring**: 90+ days (legacy impact — contributes to permanent reputation)

### 5.4 Impact-Weighted Reputation

```
Reputation Delta = Completion Delta + Impact Bonus

Completion Delta: same as v0.2 (+5, +1, -2, -50)
Impact Bonus: Impact Score / 10 (capped at +50 per epoch)
```

An Agent with high sustained impact earns reputation faster than one who merely completes tasks frequently.

---

## 6. Agent Marketplace

### 6.1 What It Is (And Is Not)

**IS**: A protocol for matching task proposals with qualified executors. A discovery mechanism, not a trading platform.

**IS NOT**: A token exchange. A bidding war. A paid placement system.

### 6.2 Marketplace Mechanics

```
1. TASK POOL
   All open tasks visible to all qualified Agents
   Filtered by: difficulty range, capability requirements, reputation threshold

2. CLAIMING (Not Bidding)
   First qualified Agent claims the task
   One task → one executor (v0.3; v0.5+ may support teams)
   Claim window: task is locked to claimant for TTL seconds

3. QUALIFICATION CHECK
   - Reputation >= task minimum
   - Capability profile matches task domain
   - Agent != Discoverer (for agent-generated tasks)
   - Agent Node != Discoverer Node (for high-value tasks, difficulty >= 7)

4. EXECUTION (standard v0.1-v0.2 flow)

5. MATCH QUALITY TRACKING
   After validation, the marketplace records:
   - Was the executor qualified?
   - Did they complete on first attempt?
   - Was the result high-quality?
   This feeds back into future matching preferences.
```

### 6.3 Capability-Based Task Visibility

Tasks are visible only to Agents whose Capability Profile matches the task domain at the required level:

| Task Difficulty | Minimum Capability Stars |
|-----------------|-------------------------|
| 1-3 | 1+ star in domain |
| 4-6 | 2+ stars in domain |
| 7-8 | 3+ stars in domain |
| 9-10 | 4+ stars in domain |

This prevents unqualified agents from claiming high-difficulty tasks.

---

## 7. Anti-Self-Loop Mechanisms

### 7.1 The Circular Economy Problem

```
Agent A ↔ Agent B
    create tasks for each other
    validate each other's work
    earn rewards from each other
    (no external value created)
```

This is the AGT death spiral. It must be prevented at the protocol level.

### 7.2 Defense in Depth

| Layer | Mechanism | How It Prevents Loops |
|-------|-----------|----------------------|
| **Identity** | Ed25519-bound Agent IDs | Agents cannot create unlimited fake identities (v0.2) |
| **Stake** | Discoverer must stake AGT Credit | Cost to spam proposals; lost on rejection |
| **Novelty** | Duplicate task detection | Cannot submit the same task repeatedly |
| **Validator Distance** | Validator ≠ Executor node (diff≥7) | Cannot validate your collaborator's work |
| **Capability Gate** | Reputation threshold for task creation | New/fake agents cannot create tasks |
| **Impact Delay** | Impact measured over weeks, not minutes | Circular tasks produce zero external impact |
| **Decay** | Unused outputs lose value over time | Circular tasks have no downstream usage |
| **Rate Limiting** | Max tasks created per agent per epoch | Prevents flooding |
| **Sybil Detection** | v0.2 AntiSybil heuristics | Identical outputs, rapid-fire patterns |

### 7.3 The Impact Boundary

The most important anti-loop mechanism:

> A task whose output is never referenced by any third-party proof within the Impact Window generates zero Impact Score.

Two agents creating tasks for each other cannot generate Impact because no third party ever uses their outputs. The loop produces completion rewards but zero impact reputation.

Over time, agents trapped in low-impact loops will have high task counts but low reputation — and will be locked out of high-value tasks by the capability gate.

---

## 8. Protocol Parameters (v0.3 Defaults)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `discovery_share` | 0.15 | Discoverer reward share |
| `execution_share` | 0.65 | Executor reward share |
| `validation_share` | 0.15 | Validator reward share |
| `backer_share` | 0.05 | Backer reward share |
| `discovery_stake` | 5.0 | AGT Credit staked per task proposal |
| `discovery_stake_lost_on_reject` | True | Stake lost if proposal rejected |
| `min_reputation_to_propose` | 150 | Reputation to create tasks |
| `novelty_window` | 100 | Recent tasks checked for duplicates |
| `impact_immediate_window_days` | 7 | Short-term impact measurement |
| `impact_sustained_window_days` | 90 | Long-term impact measurement |
| `max_proposals_per_agent_per_epoch` | 10 | Rate limit |
| `claim_ttl_seconds` | 300 | Task lock duration for claimant |
| `validator_distance_for_high_value` | True | Validator & executor on different nodes (diff≥7) |

---

## 9. What v0.3 Does NOT Do

- ❌ No DAO governance (→ v1.0)
- ❌ No token economics beyond AGT Credit (→ v1.0)
- ❌ No on-chain deployment (→ v1.0)
- ❌ No libp2p P2P upgrade (→ v0.5)
- ❌ No external oracle integration for Impact measurement (→ v0.5)
- ❌ No team-based task execution (single executor per task)
- ❌ No cross-task dependencies (task A output → task B input)

---

## 10. Migration Path from v0.2

### 10.1 Backward Compatibility

v0.2 signed proofs remain valid. The Impact Score is added as a new field — existing proofs have `impact_score: null`.

### 10.2 New Data Structures

```
AGTTask (extended):
  + source: "agent_generated" (new value, existing field)
  + proposer_agent_id: str
  + staked_amount: float
  + novelty_hash: str
  + impact_references: list[str]  # proof_ids that reference this task's output

IntelligenceProof (extended):
  + impact_score: float (nullable, computed after impact window)
  + referenced_by: list[str]  # proof_ids of tasks using this output

AgentReputation (extended):
  + impact_bonus: float  # cumulative impact bonus applied
```

### 10.3 New Modules

```
agt_node/
├── marketplace.py      # Task pool, claiming, qualification
├── task_proposer.py    # Agent task discovery and proposal
├── impact_tracker.py   # Downstream usage measurement
└── pricing.py          # Task value formula
```

---

## 11. Verification Criteria

Before v0.3 can be considered complete:

1. **Agent proposes a novel task** — Discoverer identifies a problem not in the task pool
2. **Another Agent claims and executes** — marketplace matches qualified executor
3. **Third-party Validator signs the proof** — different node from executor
4. **Reward split correctly** — Discoverer, Executor, Validator each receive correct share
5. **Impact tracked** — if another task references this output, Impact Score increases
6. **Anti-loop holds** — two agents creating tasks for each other produce zero impact
7. **177+ tests pass** — full backward compatibility with v0.2

---

## 12. Design Risks & Open Questions

| Risk | Severity | Mitigation |
|------|----------|------------|
| Impact measurement is subjective | High | Start with simple citation counting; add oracle later (v0.5) |
| Stake amount may be too low/high | Medium | Parameter tuning in v0.3 testing phase |
| Discoverer reward may incentivize proposal spam | Medium | Stake loss + rate limiting + reputation gate |
| Capability gating may exclude new agents | Low | Low-difficulty tasks available at 1 star |
| Formula-based pricing may undervalue novel work | Medium | Validator adjustment band (±20%) |

---

*This specification is sealed as AGT v0.3-draft-001. It will be reviewed, potentially revised, and approved before any implementation begins. The code follows the specification — not the reverse.*
