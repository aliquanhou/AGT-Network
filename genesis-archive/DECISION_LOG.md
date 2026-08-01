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

---

## Design Principles (Updated for v0.2)

1. **Proof Before Token** — unchanged
2. **Record Before Reward** — unchanged
3. **Verify Before Trust** — strengthened: cryptographic verification replaces heuristic trust
4. **Constrain Before Scale** — unchanged
5. **Preserve the Origin** — strengthened: genesis proof in same ledger as all contributions
6. **Identity Is Earned** — reputation is non-transferable, proof-backed, cryptographically bound
7. **Trust Is Verifiable** — any node can independently verify any proof's signature
