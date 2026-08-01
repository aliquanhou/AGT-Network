# AGT Network — Protocol Specification

**AGT Protocol v1.0.0 (Genesis)**
**Reference Implementation**: v0.36.1

---

## What This Is

This directory contains the **normative protocol specification** for the AGT Network. These documents define the AGT protocol in a language-agnostic, implementation-independent manner.

The reference implementation (`D:\claude\AGT-Network`) is a Python demonstration of the protocol. **The specification is authoritative.** Where the reference implementation and a specification disagree, the specification defines the correct behavior.

## Why This Exists

> When the protocol is defined independent of any single implementation, it can be re-implemented in any language by any party. This is what transforms a "software project" into a "protocol."

## Specifications

| Number | Title | Status | Core Concept |
|--------|-------|--------|--------------|
| [AGN-000](AGN-000.md) | Specification Conventions | Final | Normative language, versioning, data types |
| [AGN-001](AGN-001.md) | Agent and Node Identity | Final | Ed25519 key pairs, agent ID derivation |
| [AGN-002](AGN-002.md) | Intelligence Ledger | Final | Block structure, hash chain, persistence |
| [AGN-003](AGN-003.md) | Intelligence Proof (PoI) | Final | Proof structure, scoring, signatures |
| [AGN-004](AGN-004.md) | Impact Score | Final | Downstream value measurement, epochs |
| [AGN-005](AGN-005.md) | Agent Reputation | Final | Soulbound model, traceability, levels |
| [AGN-006](AGN-006.md) | P2P Protocol | Final | UDP discovery, WebSocket, message types |
| [AGN-007](AGN-007.md) | Protocol Fee | Final | Fee schedule, Genesis Vault, vesting |

## How to Use

### Implementing the Protocol

To implement AGT in a new language, read the specifications in order:

1. Start with AGN-000 (conventions)
2. Implement AGN-001 (identity) — foundational for everything else
3. Implement AGN-003 (proofs) — the core data structure
4. Implement AGN-002 (ledger) — where proofs are recorded
5. Implement AGN-004 (impact) and AGN-005 (reputation) — economic layers
6. Implement AGN-006 (P2P) — network communication
7. Implement AGN-007 (fees) — protocol economics

### Verifying Compatibility

A compatible implementation MUST:
- Produce identical `block_hash` values for identical input data
- Verify Ed25519 signatures created by any other implementation
- Reject self-validation (AGN-003 §6.3)
- Enforce the supply guard (AGN-002 §7)
- Preserve the Genesis Block (AGN-002 §2.2)

## Relationship to AIPs

Changes to these specifications proceed through the AIP process (see `../aip/AIP-0.md`). A specification change that alters protocol behavior requires a Core AIP.

## Reference Implementation

The Python reference implementation maps to specifications as follows:

| Specification | Reference Module |
|---------------|-----------------|
| AGN-001 | `agt_node/identity.py`, `agt_node/agent_identity.py` |
| AGN-002 | `reward_ledger/ledger.py` |
| AGN-003 | `poi_consensus/intelligence_proof.py`, `poi_consensus/scorer.py` |
| AGN-004 | `impact_oracle/signals.py`, `impact_oracle/scoring.py`, `impact_oracle/epoch.py` |
| AGN-005 | `agt_node/reputation.py` |
| AGN-006 | `p2p_network/discovery.py`, `p2p_network/connection.py`, `p2p_network/protocol.py` |
| AGN-007 | `reward_ledger/economy/protocol_fee.py` |

## Versioning

The protocol version follows Semantic Versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible changes (e.g., change to PoI formula)
- **MINOR**: Backward-compatible extensions (e.g., new signal type)
- **PATCH**: Clarifications only

Current protocol version: **1.0.0 (Genesis)**

---

*"If you can implement AGT from these specifications alone, without reading the reference implementation, then AGT is a protocol. If you cannot, then AGT is still just a Python project."*
