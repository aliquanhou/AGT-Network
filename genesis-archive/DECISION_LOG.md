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

### Decision #18: v0.3 Implementation Order Adjusted — Impact Oracle First

**Context**: Architecture review determined that Impact Oracle is the load-bearing economic defense. Autonomous features without Impact measurement = car without brakes.

**Decision**: v0.3 implementation order:
1. Impact Oracle Core (signals, scoring, epoch system, cycle detection)
2. Autonomous Task Generator (opportunity detection, task proposal, novelty check)
3. Agent Marketplace (claiming, qualification, matching)
4. Protocol Fee Engine (2% fee, Genesis Vault, 20-year release schedule)
5. Economic Simulation (controlled environment with monitoring)
6. 1000 Agent Stress Test (random attacks, random cooperation, 10,000 epochs)

**Reasoning**:
- "v0.3 决定 AGT 有没有经济生命"
- Impact measurement must work before agents can autonomously create tasks
- Simulation before open network prevents economic collapse in production

**Approved**: Genesis Team

### Decision #19: Genesis Vault Replaces Direct Attribution

**Context**: Direct credit of 0.5% fee to a personal address could be perceived as founder enrichment.

**Decision**: Replace direct Genesis Attribution with **Genesis Vault**:
- 0.5% Protocol Fee flows into Genesis Vault (smart contract in v1.0, simulated in v0.3)
- 20-year linear release schedule to Genesis Architect
- Vault address: `agt-genesis-vault-000000000000`
- Maximum lifetime attribution unchanged: 5,000,000 AGT

**Reasoning**:
- "协议创始人的价值来自长期维护" — long-term alignment, not short-term extraction
- 20-year vesting proves commitment to protocol longevity
- Vault is transparent and auditable
- Avoids "Founder Mining" / "Founder Tax" language — use "Genesis Contribution Attribution"

**Approved**: Genesis Team

**Impact**: `economy/allocation.py` will implement GenesisVault with vesting schedule.

### Decision #21: Protocol Freeze — AIP Governance Established

**Context**: v0.36 is complete. The protocol has 8 versions, 285 tests, and public-ready deployment. Continued rapid iteration on core rules would undermine protocol trust.

**Decision**: 
1. **Protocol Freeze**: 8 core components frozen. Changes require a Core AIP.
2. **AIP Governance**: All protocol changes proceed through the AGT Improvement Proposal process (AIP-0).
3. **v0.36.x**: Bug fixes, docs, deployment, and tests only. No new protocol features.
4. **AIP-1**: Formal declaration of Genesis Phase completion.

**Frozen components**: PoI formula, Reputation model, Ledger structure, Impact scoring, Protocol Fee, Identity, Validator rules, Signal weights.

**Non-frozen**: Dashboard, API, SDK, examples, Docker, docs, tests, bug fixes, performance.

**Reasoning**:
- "协议需要稳定。协议不是靠自己证明。协议靠别人愿意使用证明。"
- A protocol that changes weekly cannot be relied upon by strangers
- The AIP process mirrors successful open protocols (Bitcoin BIP, Ethereum EIP)
- Protocol freeze doesn't mean development stops — it means changes are deliberate, transparent, and reviewed

**Approved**: Genesis Architecture

**Impact**: v0.36.x is the stabilization branch. v0.5+ requires AIPs for any protocol change.

**Context**: The protocol has 177 tests, Ed25519 trust, economic specifications. What is the singular goal of v0.3?

**Decision**: The acceptance criterion for v0.3 is:

> **Let one AI node produce an undeniable proof of real value creation.**

Not: run 10,000 tasks. Not: issue X AGT Credit. Not: have Y agents.

One proof. Undeniably real. Independently verifiable. Measurably impactful.

**Reasoning**:
- "下一步不要追求代码量。追求让第一个AI节点产生一个无法被否认的真实价值证明。"
- This would be AGT's true Genesis Moment
- Everything else — marketplace, automation, scaling — serves this one goal

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
