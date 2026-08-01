# Security Policy

## Reporting a Vulnerability

AGT Network is an experimental protocol. Security vulnerabilities — especially those affecting the economic model, cryptographic signatures, or ledger integrity — should be reported responsibly.

**Do NOT open a public issue for security vulnerabilities.**

Email: security@agt-network.dev (forthcoming)

Include:
- AGT version affected
- Steps to reproduce
- Potential impact on the protocol
- Suggested fix (if any)

## Supported Versions

| Version | Status |
|---------|--------|
| v0.36   | ✅ Active (Genesis Testnet) |
| v0.3    | ✅ Active |
| v0.2    | ✅ Active (Trust Layer) |
| v0.1    | ⚠ Legacy (no longer updated) |

## Security Model

AGT's security model relies on:

1. **Ed25519 Signatures** — All Intelligence Proofs are cryptographically signed
2. **Hash Chain Integrity** — Ledger blocks are chained via SHA-256
3. **Soulbound Reputation** — Reputation cannot be transferred or purchased
4. **Supply Guard** — AGT Credit issuance is capped at protocol-defined maximum
5. **Impact Oracle** — Real-world usage measurement prevents self-farming

## Known Limitations (v0.36)

- P2P layer uses UDP multicast (local network only) — libp2p upgrade in v0.5
- Validator in v0.1 single-node testing mode allows same-node validation
- Economic attack review acknowledges residual risks (see genesis-archive/ECONOMIC-ATTACK-REVIEW.md)

## Audit

A security audit was performed on v0.1 (see genesis-archive/AUDIT-v0.1.md).
All 5 findings have been resolved as of v0.2.
