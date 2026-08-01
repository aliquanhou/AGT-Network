# AGT Network — Decision Log

---

## 2026-08-01

### Decision #8: v0.2 Trust Layer — No Economic Expansion, Trust Roots Only

**Context**: After sealing v0.1.2 Genesis Archive, a decision was needed: expand economic features, or establish cryptographic trust first?

**Decision**: v0.2 implements ONLY the Trust Layer:
- Ed25519 Identity (key pairs, agent identity binding)
- Proof Signatures (validator signs every IntelligenceProof)
- Proof Verification (any node can independently verify)
- Reputation Consensus (reputation must reference signed proofs)
- Anti-Sybil Protection (agent farming detection)
- Trust Network E2E Test

**Explicitly deferred to v0.3**:
- Agent marketplace
- Agent-generated tasks
- Agent-to-agent hiring
- DAO governance
- Token economics

**Reasoning**:
- "v0.2 不增加经济模型，不发行资产，只建立 AGT 网络的信任根"
- The three medium-risk audit findings all converge on missing cryptographic trust
- Without signatures, AGT is a demo. With signatures, it's a protocol.

**Approved**: Genesis Team

**Impact**: v0.2 development scope is locked. Six implementation steps defined.

### Decision #9: Agent Identity = hash(pubkey + index), Not UUID

**Context**: v0.1 used UUID-based agent IDs with no cryptographic binding.

**Decision**: v0.2 derives agent identity from the node's Ed25519 public key:
```
agent_id = SHA-256(node_public_key + agent_creation_index)[:16]
```

**Reasoning**:
- Globally unique (cryptographic, not just random)
- Verifiable — anyone can confirm an agent belongs to a node
- No central registry needed
- Prevents identity forgery across the network

**Approved**: Genesis Team

### Decision #10: Genesis Proof as First Intelligence Record

**Context**: The Genesis Block and Genesis Identity existed separately from the Intelligence Proof system.

**Decision**: Unify them — the genesis contribution IS an Intelligence Proof (proof_id: `poi-genesis-000000000000`), recorded in the Intelligence Ledger as block 0. The GenesisIdentity is the metadata wrapper, the genesis proof is the contribution record. Both live in the same system as all other contributions.

**Reasoning**:
- "不要单独设计 Founder Wallet。Genesis Proof #000001 本身就是第一份 Intelligence Proof"
- All value contributions — from genesis to latest — on the same ledger
- Founder attribution is proven through the same mechanism as agent attribution

**Approved**: Genesis Team

### Decision #11: Soulbound Reputation — Non-Transferable, Non-Purchasable

**Context**: Reputation in v0.1 could be directly assigned (`rep.score = 9999`).

**Decision**: v0.2 reputation:
- Every reputation change must reference a signed Intelligence Proof
- Direct assignment is removed (score property becomes read-only from outside)
- Reputation cannot be transferred between agents
- Reputation cannot be purchased — only earned through verified contributions

**Reasoning**:
- "不能购买。不能转移。" (Cannot buy. Cannot transfer.)
- This mirrors the concept of soulbound tokens — identity-bound, non-transferable assets
- Reputation is the agent's permanent record, not a tradeable commodity

**Approved**: Genesis Team

### Decision #12: v0.2 Complete — Trust Layer Founded, Enter Design Phase

**Context**: v0.2 Trust Layer implemented in 4 steps: Identity → Signature → Verification + Reputation + Anti-Sybil → E2E. 177 tests pass. All 5 audit findings resolved.

**Decision**: FREEZE v0.2 codebase. DO NOT proceed to v0.3 coding. First, write the Autonomous Economy Protocol Specification.

**Reasoning**:
- "v0.2 是信任根。v0.3 是经济生命。这里设计错误，后面所有东西都会受到影响。"
- The jump from "trust verification" to "autonomous economy" is not incremental — it's a protocol behavior change
- A specification-first approach prevents the "AI self-entertainment economy" anti-pattern
- Six core design questions must be resolved before any code is written

**Approved**: Genesis Team

**Impact**: v0.3 enters SPECIFICATION PHASE. No code until the Autonomous Economy Protocol Specification is reviewed and approved.

### Decision #13: Impact Score Must Supplement Completion Score

**Context**: Current reputation model rewards task completion. But a task used by 1M people should be worth more than a task used by 1 person.

**Decision**: v0.3 will introduce **Impact Score** as a separate, time-decaying metric:
```
Impact Score = UsageCount × UsageQuality × TimeDecay
```
- UsageCount: how many agents/users use the output
- UsageQuality: how transformative the usage is (adoption vs. passing reference)
- TimeDecay: recent impact > old impact (preventing reputation from becoming a retirement asset)

**Reasoning**:
- "信誉不能只奖励'完成'。否则 AGT 会变成'制造任务机器'而不是'创造价值机器'。"
- Completion proves ability. Impact proves value. Both matter.
- Impact is measured downstream — after the contribution is published and used

**Approved**: Genesis Team

**Impact**: v0.3 PoI formula will be extended to include Impact factor. v0.2 scores remain valid (backward compatible).

### Decision #15: Impact Oracle Is the FIRST v0.3 Module

**Context**: Economic Attack Review revealed that the Impact Boundary is the load-bearing defense for 4 of 5 attack vectors. Without Impact measurement, the autonomous economy collapses into self-farming.

**Decision**: v0.3 implementation order:
1. Impact Oracle (FIRST — before any autonomous features)
2. Protocol Fee engine
3. Task Proposer
4. Agent Marketplace
5. Full Autonomous Economy integration

**Reasoning**:
- "Building autonomy without Impact is building a car without brakes"
- Every v0.3 module depends on Impact measurement for anti-gaming
- Impact Oracle must be tested with v0.2 signed proofs before autonomy begins

**Approved**: Genesis Team

### Decision #16: Protocol Fee Is a Constant, Not a Lever

**Context**: The concept of "protocol fee" could be misperceived as a founder enrichment mechanism.

**Decision**: Intelligence Protocol Fee: 2% of every task reward, hardcoded, immutable without protocol upgrade.
- Network Infrastructure: 1.0%
- Ecosystem Development: 0.5%
- Genesis Contribution Attribution: 0.5% (to public address `agt-genesis-attribution-000000000000`)

**Reasoning**:
- Mathematically bounded: max 0.5% × 1,000,000,000 = 5,000,000 AGT
- Code-auditable: fee percentage is a constant
- Transparent: all Genesis Attribution credits recorded on public ledger
- Historical precedent: Zcash Founders Reward (20%, 4 years); AGT is 0.5%, permanent
- "不要叫抽水。叫 Intelligence Protocol Fee。"

**Approved**: Genesis Team

### Decision #17: Economic Attack Review Passed — v0.3 Implementation Approved

**Context**: Five attack vectors analyzed before any v0.3 code was written.

**Decision**: v0.3 Autonomous Economy implementation is APPROVED with conditions:
1. Impact Oracle implemented FIRST
2. Protocol Fee engine implemented SECOND
3. All 177 existing tests must continue to pass
4. New anti-farming tests added for each new module

**Reasoning**:
- All 5 attack vectors have layered defenses (not single points of failure)
- The Impact Boundary is the load-bearing defense — must be built first
- No attack achieves "protocol death" — each is bounded by economic irrationality
- Residual risks are acknowledged and accepted as inherent to permissionless protocols

**Approved**: Genesis Team

---

## Design Principles (Updated for v0.3 Direction)

1. **Proof Before Token** — unchanged
2. **Record Before Reward** — unchanged
3. **Verify Before Trust** — strengthened: cryptographic verification
4. **Constrain Before Scale** — unchanged
5. **Preserve the Origin** — Genesis Architect attribution, not admin control
6. **Identity Is Earned** — Soulbound reputation, proof-backed, non-transferable
7. **Trust Is Verifiable** — any node can independently verify any proof's signature
8. **Impact Over Activity** — value is measured by downstream impact, not task count
9. **Specification Before Implementation** — design the economy before coding it
