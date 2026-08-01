# AIP-1: Protocol Freeze Declaration

**AIP Number**: AIP-1
**Title**: Protocol Freeze — Genesis Phase Completion
**Author**: Genesis Architecture
**Status**: Accepted
**Type**: Process
**Created**: 2026-08-01
**Requires**: AIP-0
**Replaces**: None

---

## Abstract

Declares the completion of the AGT Network Genesis development phase and freezes the core protocol as of v0.36. Establishes that future changes to frozen components require an accepted AIP.

## Motivation

The Genesis phase of AGT Network has produced:

- v0.1: Agent Economy Loop (Value Creation Layer)
- v0.1.1: Ledger Persistence + Supply Guard (Safety)
- v0.1.2: Genesis Archive (History)
- v0.2: Trust Layer (Ed25519, Proof Signatures, Anti-Sybil)
- v0.3: Autonomous Economy (Impact Oracle, Marketplace, Protocol Fee)
- v0.35: Public Testnet (One-click node, Docker, SDK)
- v0.36: Public Genesis Release (Smoke test, Community files, Genesis Node)

The protocol is now sufficiently defined that continued rapid iteration on core rules would undermine the trust that the protocol requires. A protocol that changes weekly cannot be relied upon.

## Specification

### Frozen Components (require Core AIP to modify)

1. `poi_consensus/intelligence_proof.py` — Proof structure and scoring formula
2. `agt_node/reputation.py` — Reputation model and events
3. `reward_ledger/ledger.py` — Ledger block structure and chain integrity
4. `impact_oracle/scoring.py` — Impact score formula
5. `impact_oracle/signals.py` — Signal weights
6. `reward_ledger/economy/protocol_fee.py` — Fee schedule and Genesis Vault
7. `agt_node/identity.py` — Ed25519 key management
8. `task_engine/validator.py` — Validator rules (self-validation block)

### Unfrozen Components (may be modified in v0.36.x)

1. `web_dashboard/` — UI improvements
2. `api_server/` — Additional API endpoints
3. `sdk/` — SDK extensions
4. `examples/` — New task examples
5. `scripts/` — Tooling
6. `docs/` — Documentation
7. Docker and deployment
8. Test files
9. Bug fixes that don't change protocol behavior
10. Performance optimizations

### Non-Frozen Protocol Extensions (Standard AIP required)

New features that extend but don't modify the core protocol:

1. New task types
2. New signal types (Tier 2, Tier 3)
3. New validator heuristics
4. Marketplace enhancements
5. P2P protocol upgrades (v0.5)

### What This Means for Contributors

- **Found a bug in the PoI formula?** → Open an issue + draft a Core AIP
- **Want to add a new task type?** → Draft a Standard AIP
- **Dashboard looks ugly?** → Just send a PR (no AIP needed)
- **Think the protocol fee should be 5%?** → Draft a Core AIP, expect significant community discussion

### Genesis Phase Achievements

| Metric | Value |
|--------|-------|
| Git commits | 21 |
| Protocol versions | 8 (v0.1 → v0.36) |
| Code lines | 13,500+ |
| Tests | 285 (all passing) |
| Modules | 14 |
| Audit findings resolved | 5/5 |
| Genesis archive documents | 13 |
| AIPs | 2 |

---

## Acceptance

Accepted by Genesis Architecture on 2026-08-01. The protocol freeze takes effect immediately.
