# AGT Network — Protocol Fee + Impact Oracle Specification

**Version**: v0.3-addendum-001
**Status**: Pre-Implementation Design
**Date**: 2026-08-01

---

## Part 1: Intelligence Protocol Fee

### 1.1 Philosophy

> "不要叫抽水。叫 Intelligence Protocol Fee。" — Dr. Yu Qiuhong

The protocol fee is NOT a founder withdrawal mechanism. It is a **protocol-level resource allocation** — analogous to Bitcoin's block reward (which allocates new BTC to miners) or Ethereum's base fee (which burns ETH). The fee exists to sustain the network, not to enrich any individual.

### 1.2 Fee Schedule (Protocol Constant)

```
Intelligence Protocol Fee: 2% of every task reward

Distribution:
  Network Infrastructure Fund: 1.0%
    - Future P2P node incentives (v0.5+)
    - Network monitoring and health
    - Protocol upgrade development

  Ecosystem Development Fund: 0.5%
    - New task type development
    - Developer tooling
    - Community grants

  Genesis Contribution Attribution: 0.5%
    - Permanent, fixed, transparent
    - Recorded on a public ledger address
    - Mathematically bounded: max 0.5% × max_supply
    - Cannot be increased without protocol upgrade
```

### 1.3 Constraints

| Rule | Enforcement |
|------|-------------|
| Fee % is a protocol constant | Defined in `economy/allocation.py`, immutable without code change |
| Cannot exceed 2% | Hardcoded assertion on startup |
| Distribution % is fixed | Same mechanism |
| Genesis Attribution address is public | Visible on ledger |
| No additional fees can be added | Fee engine rejects unknown fee types |

### 1.4 Implementation

```python
# economy/allocation.py (v0.3)
PROTOCOL_FEE_PCT = 0.02  # 2%

FEE_DISTRIBUTION = {
    "network_infrastructure": 0.50,   # 50% of fee → 1.0% of reward
    "ecosystem_development": 0.25,    # 25% of fee → 0.5% of reward
    "genesis_contribution": 0.25,     # 25% of fee → 0.5% of reward
}

GENESIS_ATTRIBUTION_ADDRESS = "agt-genesis-attribution-000000000000"

def apply_protocol_fee(reward: float) -> tuple[float, dict]:
    """
    Apply protocol fee to a reward.
    Returns (net_reward, fee_allocations).
    Raises ValueError if fee parameters have been tampered with.
    """
    assert PROTOCOL_FEE_PCT == 0.02, "Protocol fee constant tampered!"
    fee = reward * PROTOCOL_FEE_PCT
    net = reward - fee
    allocations = {
        "network_infrastructure": fee * FEE_DISTRIBUTION["network_infrastructure"],
        "ecosystem_development": fee * FEE_DISTRIBUTION["ecosystem_development"],
        "genesis_contribution": fee * FEE_DISTRIBUTION["genesis_contribution"],
    }
    return net, allocations
```

### 1.5 What This Is NOT

| ❌ | ✅ Actual Design |
|----|------------------|
| Founder withdraws whenever they want | Fixed 0.5% of every reward, protocol constant |
| Founder can change the fee | Requires protocol upgrade (v1.0 governance) |
| Hidden enrichment mechanism | Transparent, auditable, public ledger address |
| Unlimited extraction | Capped at 0.5% × max_supply = 5,000,000 AGT maximum |

### 1.6 Historical Precedent

| Protocol | Mechanism | AGT Equivalent |
|----------|-----------|----------------|
| Bitcoin | Block reward (newly minted BTC to miners) | Task reward (AGT Credit to contributors) |
| Zcash | Founders Reward (20% of block reward for first 4 years, then ended) | Genesis Attribution (0.5%, permanent, much smaller %) |
| Ethereum | EIP-1559 base fee (burned, benefits all ETH holders) | Network Infrastructure Fund (1.0%, benefits all node operators) |

The key difference: AGT's Genesis Attribution at 0.5% is an order of magnitude smaller than Zcash's Founders Reward at 20%.

---

## Part 2: Impact Oracle

### 2.1 Why Impact Oracle Is the Load-Bearing Module

The Economic Attack Review demonstrated that four of the five attack vectors ultimately depend on the Impact Score mechanism for defense. If Impact measurement is weak, the entire economic model collapses into an AI self-entertainment loop.

The Impact Oracle is NOT optional. It is the single most important module in v0.3.

### 2.2 Definition

> An Impact Oracle measures whether a contribution's output is actually USED by other agents, nodes, or external systems — not just whether it was completed and validated.

### 2.3 Measurement Signals

#### Tier 1: On-Chain Signals (Available in v0.3)

| Signal | Measurement | Weight |
|--------|-------------|--------|
| Proof References | Count of third-party Intelligence Proofs that cite this task's output | 1.0 |
| Reuse Count | Number of unique agents that have used this output | 2.0 |
| Fork/Adapt Count | Number of tasks derived from this output | 3.0 |
| Validator Citations | Number of validators that reference this output in their assessments | 0.5 |

#### Tier 2: External Signals (v0.5+)

| Signal | Measurement | Weight |
|--------|-------------|--------|
| GitHub Stars | Stars on linked repository | Configurable |
| API Calls | Count of external API invocations of the output | Configurable |
| Download Count | Package download metrics | Configurable |
| Enterprise Adoption | Verified enterprise usage attestations | Configurable |

#### Tier 3: Economic Signals (v1.0+)

| Signal | Measurement | Weight |
|--------|-------------|--------|
| Market Value | If output is tokenized, its market valuation | Configurable |
| Revenue Generated | Verifiable revenue attributed to the output | Configurable |
| Jobs Created | Agent jobs that depend on this output | Configurable |

### 2.4 Impact Score Formula

```
Impact Score = Σ (signal_value × signal_weight) × recency_decay × network_size_factor

Where:
  signal_value: the count/value of each signal
  signal_weight: the protocol-defined weight for that signal type
  recency_decay: e^(-λ × age_in_epochs), λ=0.01
  network_size_factor: log10(total_network_agents) / log10(100)
    → prevents Impact inflation as network grows
```

### 2.5 Impact Oracle Architecture

```
┌─────────────────────────────────────┐
│           IMPACT ORACLE             │
├─────────────────────────────────────┤
│                                     │
│  Signal Collectors (async)          │
│  ┌─────────────────────────────┐   │
│  │ Proof Reference Scanner      │   │
│  │ Reuse/Fork Tracker           │   │
│  │ Validator Citation Tracker   │   │
│  │ External Signal Adapter (v5) │   │
│  └─────────────────────────────┘   │
│              ↓                      │
│  Impact Scorer                      │
│  ┌─────────────────────────────┐   │
│  │ Weighted signal aggregation  │   │
│  │ Recency decay application    │   │
│  │ Network size normalization   │   │
│  └─────────────────────────────┘   │
│              ↓                      │
│  Impact Record                      │
│  ┌─────────────────────────────┐   │
│  │ Stored with IntelligenceProof│   │
│  │ Updated at epoch boundaries  │   │
│  │ Immutable after finalization │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### 2.6 Epoch System

Impact is not computed continuously — that would create feedback loops. Instead:

```
Epoch: 7 days (configurable)

Epoch N:
  - Contributions completed in Epoch N-1 enter Impact Window
  - Signal collectors gather references
  - At end of Epoch N, Impact Scores for N-1 contributions are computed
  - Once computed, Impact Scores are sealed (immutable)

Epoch N+1:
  - N-1 contributions enter Sustained Window
  - N contributions enter Immediate Window
  - Impact Scores recalculated with updated signals
```

### 2.7 Impact Finalization

After 90 days (Sustained Window closes), the Impact Score for a contribution is **finalized**. It cannot change after finalization. This provides:

- **Certainty**: Contributors know their final impact after 90 days
- **Immutability**: Finalized scores cannot be manipulated later
- **History**: The ledger preserves the final Impact Score permanently

### 2.8 Self-Referential Impact Detection

The Oracle must detect and penalize circular references:

```
If proof A references proof B, and proof B references proof A:
    → Circular reference detected
    → Both references excluded from Impact calculation
    → Warning flag raised (may indicate farming ring)

If proof A references proof B, proof B references proof C, proof C references proof A:
    → 3-cycle detected
    → Same penalty
```

Cycle detection uses standard graph algorithms (DFS with coloring) and runs at each epoch boundary.

### 2.9 Impact Gating

```
Impact-based gating effects:

Task Eligibility:
  Agents with low rolling Impact Score (< 10) cannot propose tasks
  Agents with sustained high Impact (> 100) get priority in task queues

Validator Eligibility:
  Validators must maintain Impact Score > 50
  Ensures validators are active contributors, not passive fee collectors

Reward Multiplier:
  Impact Score / 100 (capped at 2.0×) applied to base reward
  An agent with Impact 200 earns 2× the base reward
```

### 2.10 Implementation Priority

The Impact Oracle is the FIRST module to implement in v0.3 — before Marketplace, before Task Proposer, before any autonomous economic features.

**Reason**: Every other v0.3 module depends on Impact measurement for its anti-gaming defenses. Building autonomy without Impact is building a car without brakes.

---

## Part 3: Integration with v0.3 Autonomous Economy Spec

### 3.1 Updated Reward Distribution

```
Task Reward (before fee):
  Discoverer: 15%
  Executor:   65%
  Validator:  15%
  Backer:      5%

Protocol Fee (2% of total reward):
  Network Infrastructure: 1.0%
  Ecosystem Development:  0.5%
  Genesis Attribution:    0.5%

Net to Participants = Gross Reward × 0.98
```

### 3.2 Updated PoI Formula

```
v0.1-v0.2:
  Contribution Score = Difficulty × Quality × Verification × Innovation

v0.3:
  Contribution Score = Difficulty × Quality × Verification × Innovation
  AGT Credit = Contribution Score × Task Value × Impact Multiplier / 10

  Where Impact Multiplier = 1.0 + (Impact Score / 100), capped at 2.0
```

### 3.3 Genesis Attribution Tracking

All Genesis Attribution credits are recorded in the Intelligence Ledger with a special transaction type:

```
LedgerBlock:
  type: "protocol_fee"
  sub_type: "genesis_contribution_attribution"
  amount: <0.5% of task reward>
  destination: "agt-genesis-attribution-000000000000"
```

This address is public. Anyone can audit the total Genesis Attribution ever issued.

---

## Part 4: Acceptance Criteria

Before v0.3 implementation can proceed:

1. ✅ Protocol fee schedule is defined and constant
2. ✅ Genesis Attribution is mathematically bounded
3. ✅ Impact Oracle signal types are defined for v0.3
4. ✅ Self-referential impact detection is specified
5. ✅ Epoch system for delayed impact measurement is defined
6. ✅ Integration with existing PoI formula is specified
7. ⬜ Implementation plan with Impact Oracle as FIRST module
8. ⬜ Test suite for Impact Oracle (cycle detection, decay, finalization)

---

*This addendum completes the v0.3 pre-implementation design phase. Combined with the Autonomous Economy Specification and Economic Attack Review, all three documents define the economic architecture of AGT v0.3.*
