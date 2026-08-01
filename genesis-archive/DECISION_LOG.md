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

### Decision #14: The Founder Role Is "Genesis Architect", Not "Key Holder"

**Context**: Multiple decisions have reinforced that Genesis Identity is NOT an admin role. The name should reflect this.

**Decision**: The official designation for the human founder in all AGT documentation is:

> **Genesis Architect** — the human who initiated the first Agent Economy Protocol specification.

Not: admin, owner, key holder, super-user, or privileged account.

**Reasoning**:
- "不是'拥有钥匙的人'。而是创造第一套 AI贡献证明经济协议的人。"
- The Genesis Architect designed the protocol. The protocol now runs independently.
- Attribution without control — the founding principle of AGT

**Approved**: Genesis Team

**Impact**: All future documentation uses "Genesis Architect" for the human founder role.

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
