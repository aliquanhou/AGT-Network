# AIP-0: AGT Improvement Proposal Process

**AIP Number**: AIP-0
**Title**: AGT Improvement Proposal Process
**Author**: Genesis Architecture
**Status**: Accepted
**Type**: Process
**Created**: 2026-08-01
**Requires**: None
**Replaces**: None

---

## Abstract

This AIP establishes the formal process for proposing, discussing, reviewing, and accepting changes to the AGT Network protocol. It defines the AIP lifecycle, document structure, and acceptance criteria.

## Motivation

Protocols are not software projects. Software iterates continuously; protocols must be stable enough to be trusted by strangers.

As of v0.36, AGT Network has:

- A defined consensus mechanism (Proof of Intelligence)
- A trust layer (Ed25519 identity + proof signatures)
- An economic model (Agent → Task → Validation → Impact → Reward)
- A reference implementation (13,500+ lines, 285 checks passing)
- A public testnet-ready release

With the completion of the Genesis phase, the protocol must now transition from "active development" to "governed evolution." Changes to core protocol rules must be deliberate, transparent, and community-reviewed.

## Specification

### AIP Lifecycle

```
Draft → Discussion → Review → Accepted / Rejected → Implementation
```

1. **Draft**: Author writes a proposal following the AIP template.
2. **Discussion**: Proposal is opened as an issue or PR for community feedback (minimum 14 days).
3. **Review**: At least 2 maintainers review. For protocol-level changes (`type: Core`), at least one review must be from outside the original development team.
4. **Decision**: Proposal is accepted, rejected, or returned for revision.
5. **Implementation**: Accepted proposals are implemented and merged. The AIP status is updated.

### AIP Types

| Type | Scope | Review Required |
|------|-------|-----------------|
| **Core** | PoI formula, Reputation model, Ledger structure, Impact scoring, Protocol Fee | 2+ maintainers |
| **Standard** | New task types, new signal types, marketplace rules, SDK APIs | 1+ maintainer |
| **Process** | Governance, contribution guidelines, release procedures | 1+ maintainer |
| **Informational** | Design rationale, research, background | None |

### Protocol Freeze

The following components are **frozen** as of v0.36. Changes require a **Core AIP** and community consensus:

1. **Proof of Intelligence formula**: `Contribution Score = Difficulty × Quality × Verification × Innovation`
2. **Reputation Model**: Soulbound, 7-tier, proof-referenced, non-transferable
3. **Intelligence Ledger**: Hash-chained blocks, persistent, supply-guarded
4. **Impact Score**: `Usage × Verification × Longevity × Diversity`, Epoch-delayed measurement
5. **Protocol Fee**: 2% fixed constant, Genesis Vault 20-year vesting

Changes to these components without an accepted AIP shall be considered a protocol fork.

### Non-Frozen Components

The following may be modified without an AIP during the testnet phase (v0.36.x):

- Bug fixes (no protocol behavior change)
- Documentation improvements
- Deployment and tooling (Docker, scripts, SDK)
- Test coverage
- Dashboard UI
- Performance optimizations
- Error messages and logging

### AIP Template

All AIPs must follow this structure:

```markdown
# AIP-N: Title

**AIP Number**: AIP-N
**Title**: (short description)
**Author**: (name or GitHub handle)
**Status**: Draft
**Type**: Core | Standard | Process | Informational
**Created**: (date)
**Requires**: (AIP-N or "None")
**Replaces**: (AIP-N or "None")

## Abstract
(1-2 sentence summary)

## Motivation
(Why is this change needed? What problem does it solve?)

## Specification
(Detailed technical specification of the change)

## Rationale
(Why this approach over alternatives?)

## Backward Compatibility
(How does this affect existing proofs, ledgers, agents?)

## Test Cases
(How can this change be verified?)

## Implementation
(Reference to PR or branch, if available)
```

### AIP Registry

All AIPs are tracked in `aip/REGISTRY.md`. Accepted AIP numbers are never reused.

### Copyright

All AIPs are released under the same license as AGT Network (MIT).

---

## Acceptance

This AIP defines its own acceptance criteria and is therefore self-referential. It was reviewed and accepted by the Genesis Architecture on 2026-08-01.
