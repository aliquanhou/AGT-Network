# AGT Network v0.2 — Trust Layer (Design Outline)

**Status**: Design Outline — NOT implemented
**Target**: After v0.1.2 Genesis Review approval

---

## Why "Trust Layer"

v0.1 proved: **An Agent can create value and be rewarded.**

v0.2 must answer: **Why should anyone believe it?**

The three medium-risk audit findings from v0.1 all converge on the same problem:

| Finding | Root Cause | Solution |
|---------|-----------|----------|
| Proof not traceable to author | No cryptographic signature | Ed25519 key pairs |
| Identity not unique across network | UUID only, no binding | Public Key Infrastructure |
| Reputation can be locally forged | No cross-node consensus | Multi-node reputation verification |

These are not three separate features. They are one capability:

> **Cryptographic Trust**

---

## Layer Architecture

```
┌──────────────────────────────────────────┐
│              v0.2 TRUST LAYER             │
├──────────────────────────────────────────┤
│                                          │
│  Agent Identity                          │
│  ┌─────────────────────────────────┐    │
│  │ node_pubkey (Ed25519)            │    │
│  │ agent_index                      │    │
│  │ agent_id = hash(pubkey + index)  │    │
│  │ capability_manifest (optional)    │    │
│  └─────────────────────────────────┘    │
│                  ↓                       │
│  Cryptographic Proof                     │
│  ┌─────────────────────────────────┐    │
│  │ Validator signs IntelligenceProof│    │
│  │ signature = sign(proof_hash, sk) │    │
│  │ verify(signature, proof, pk) → ✓ │    │
│  └─────────────────────────────────┘    │
│                  ↓                       │
│  Reputation Consensus                    │
│  ┌─────────────────────────────────┐    │
│  │ Reputation Δ must reference      │    │
│  │ a signed IntelligenceProof       │    │
│  │ Multiple validators contribute   │    │
│  │ to reputation scoring            │    │
│  └─────────────────────────────────┘    │
│                                          │
└──────────────────────────────────────────┘
```

---

## Component Specs

### 1. Agent Identity (Ed25519)

```
Key Generation:
    node generates Ed25519 key pair on first launch
    private key stored locally (never transmitted)
    public key registered in NodeIdentity

Agent Identity Derivation:
    agent_id = SHA-256(node_public_key + agent_creation_index)
    → globally unique, cryptographically bound to owner node

Message Signing:
    all P2P messages include sender_signature
    receivers verify against known public keys
```

### 2. Proof Signatures

```
IntelligenceProof Extension:
    existing: proof_hash = SHA-256(core fields)
    new: validator_signature = Ed25519.sign(proof_hash, validator_sk)
    new: worker_signature = Ed25519.sign(proof_hash, worker_sk) [optional]

Verification:
    any node can call:
        verify_proof(proof, validator_pk) → bool
        → recomputes proof_hash
        → verifies signature against hash
        → confirms validator identity
```

### 3. Reputation Consensus

```
Reputation Model Upgrade:
    reputation changes must reference a signed IntelligenceProof
    reputation = aggregate of validated contributions only
    no direct assignment allowed (remove score setter)

Cross-Node Consensus:
    v0.2: simple majority among connected validators
    v0.5+: BFT consensus on reputation state

Reputation API:
    get_reputation(agent_id) → {score, level, proof_refs[]}
    → every change is traceable to a signed proof
```

---

## What v0.2 Does NOT Do

- ❌ No token issuance
- ❌ No blockchain deployment
- ❌ No DAO governance
- ❌ No agent marketplace
- ❌ No task autonomy (→ v0.3)

---

## Migration from v0.1

```
v0.1 Ledger blocks:
    IntelligenceProof without signatures
    → remain valid as "unsigned historical records"
    → marked as pre-trust-layer

v0.2 Ledger blocks:
    IntelligenceProof with validator_signature
    → verifiable authorship
    → reputation changes cryptographically bound to proofs
```

Backward compatible. v0.1 proofs are not invalidated — they are recognized as pre-signature history.

---

## Success Criteria

1. Generate Ed25519 key pair on node start → `NodeIdentity.public_key` is populated
2. Validator signs every IntelligenceProof → `validator_signature` field present
3. Any node can verify a proof's signature → `verify_proof()` returns correct result
4. Reputation changes are cryptographically traceable → every reputation delta has a `proof_ref`
5. Tests: signature generation, verification, forgery detection, reputation traceability
6. Full suite maintains 100% pass rate

---

*This is a design outline, not an implementation plan. Development begins after Genesis Review approval.*
