# Changelog

All notable changes to the AGT Network protocol.

---

## [v0.36] — 2026-08-01

### Added
- Smoke test: `python scripts/smoke_test.py` verifies complete economic loop
- GitHub community files: LICENSE (MIT), SECURITY.md, CODE_OF_CONDUCT.md
- Genesis Node permanent record with cryptographic identity
- Unified version stamp across all modules (VERSION file)
- Release notes with verification checklist

### Changed
- README updated with smoke test instructions

---

## [v0.35] — 2026-08-01

### Added
- One-click node launch: `start.bat` (Windows), `start.sh` (Linux/Mac)
- Docker support: `Dockerfile` + `docker-compose.yml`
- AGT SDK (`sdk/`): Python client with `AGTClient` class
- Real-world task examples (`examples/`)
- GitHub Actions CI (`.github/workflows/test.yml`)
- Documentation: `docs/TUTORIAL.md`, `CONTRIBUTING.md`

### Changed
- README rewritten for global developer audience

---

## [v0.3] — 2026-08-01

### Added
- **Impact Oracle** (`impact_oracle/`): Impact = Usage × Verification × Longevity × Diversity
- **Autonomous Task Generator** (`agt_node/autonomous/`): Agent-driven value discovery
- **Agent Marketplace**: Task pool, claiming, capability-based matching
- **Protocol Fee Engine**: 2% Intelligence Protocol Fee with Genesis Vault
- **Economic Attack Review**: 5 attack vectors analyzed, all with layered defenses
- Economic simulation + 1000-agent stress test (15 tests)

### Changed
- Reputation now soulbound with mandatory proof_id references
- PoI formula extended with Impact Multiplier
- 269 tests (+92 from v0.2)

---

## [v0.2] — 2026-08-01

### Added
- **Ed25519 Identity Layer**: `KeyPair`, `NodeIdentity`, `AgentIdentity`
- **Proof Signatures**: Validator signs every `IntelligenceProof`
- **Proof Registry**: Cross-node independent verification
- **Anti-Sybil Protection**: Duplicate output, rapid-fire, excessive agent detection
- **Soulbound Reputation**: Non-transferable, proof-backed
- 177 tests (+57 from v0.1.2)

### Security
- All 5 v0.1 audit findings resolved

---

## [v0.1.2] — 2026-08-01

### Added
- Genesis Archive: Whitepaper, Architecture, Audit, Genesis Record, Decision Log
- Genesis Review: Design freeze with 3 core questions

---

## [v0.1.1] — 2026-08-01

### Added
- **Ledger Persistence**: Blocks saved to `ledger_blocks.jsonl`, full restart recovery
- **Reward Supply Guard**: `max_supply` enforcement, `supply_remaining()` API

### Security
- Fixed P0-1 (Ledger not persistent)
- Fixed P0-2 (Reward inflation unbounded)

---

## [v0.1] — 2026-08-01

### Added
- Initial AGT Network Genesis Prototype
- Agent Runtime (LLM + Tools + Planner + Executor)
- P2P Network (UDP Discovery + WebSocket)
- Task Engine (4 Genesis Tasks + Validator)
- POI Consensus (Proof of Intelligence)
- Intelligence Ledger (hash-chained blocks)
- API Server + Web Dashboard
- 114 tests, all passing
