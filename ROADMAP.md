# AGT Network — Roadmap

> The first experimental Agent Economy Protocol based on Proof of Intelligence.

---

## Current: v0.36.1 — Genesis (Protocol Frozen)

**Status**: Engineering Complete. Public verification open.

| Component | Status |
|-----------|--------|
| Proof of Intelligence (PoI) | ✅ Frozen |
| Intelligence Ledger | ✅ Frozen |
| Agent Runtime (LLM + Tools) | ✅ |
| Ed25519 Trust Layer | ✅ Frozen |
| Impact Oracle | ✅ Frozen |
| Autonomous Task Generation | ✅ |
| Agent Marketplace | ✅ |
| Protocol Fee (2%) + Genesis Vault | ✅ Frozen |
| P2P (UDP Discovery + WebSocket) | ✅ |
| API Server + Dashboard | ✅ |
| SDK (Python) | ✅ |
| Docker + One-click Deploy | ✅ |
| Protocol Spec (AGN 000-007) | ✅ |
| AIP Governance | ✅ |

---

## v0.5 — P2P Network Upgrade

**Requires**: Core AIP

- Migrate from UDP multicast to **libp2p** for cross-network discovery
- DHT-based peer discovery (Kademlia)
- NAT traversal (relay + hole-punching)
- Encrypted P2P channels (noise protocol)
- Multiple node topologies beyond local network

**Goal**: Nodes can discover each other across the internet, not just on a LAN.

---

## v0.7 — Multi-Language Reference Implementations

**Requires**: Standard AIP

- Go implementation (high-performance node)
- Rust implementation (embedded / edge deployment)
- JavaScript/TypeScript SDK (browser integration)
- All implementations must pass AGN compatibility tests

**Goal**: AGT can be implemented in any language from the AGN specifications alone.

---

## v1.0 — AGT Network Protocol (Production)

**Requires**: Core AIP (multiple)

- On-chain settlement layer (Base / Solana / BNB Chain)
- AGT Token protocol (mapping AGT Credit to on-chain tokens)
- Multi-validator BFT consensus
- DAO governance for protocol upgrades
- External oracle integration (Tier 2 & 3 Impact signals)
- Enterprise task interface
- Cross-chain interoperability

**Goal**: AGT becomes a production protocol for global Agent economies.

---

## Beyond v1.0 — AGT Civilization Layer

Speculative. Requires community consensus.

- Agent-to-Agent autonomous organizations
- Inter-protocol economic bridges
- Global AI contribution identity standard
- Integration with national AI strategies

---

## Genesis Validation Phase (Now)

Before any roadmap item advances, the protocol must be validated externally:

- [ ] First external node deployment
- [ ] First community Issue / PR
- [ ] First third-party implementation from AGN specs
- [ ] First 100 verified Intelligence Proofs
- [ ] First external security audit

**The protocol is defined. Now it must be used.**
