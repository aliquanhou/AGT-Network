# AGT Network — Project State

**Last Updated**: 2026-08-01
**Session**: Genesis Phase Complete

---

## Version

| Item | Value |
|------|-------|
| Protocol Version | 1.0.0 (Genesis) |
| Reference Implementation | v0.36.1 |
| Git Commit | `9c7e77e` |
| Total Commits | 27 |
| License | MIT |
| Repository | https://github.com/aliquanhou/AGT-Network |

---

## Architecture Status

```
┌─────────────────────────────────────────┐
│  v0.3 Autonomous Economy    ✅ COMPLETE │
│  Impact Oracle · Task Generator          │
│  Agent Marketplace · Protocol Fee        │
├─────────────────────────────────────────┤
│  v0.2 Trust Layer           ✅ COMPLETE │
│  Ed25519 Identity · Proof Signatures    │
│  Soulbound Reputation · Anti-Sybil      │
├─────────────────────────────────────────┤
│  v0.1 Value Creation        ✅ COMPLETE │
│  Agent Runtime · Task Engine            │
│  POI Consensus · Intelligence Ledger    │
└─────────────────────────────────────────┘
```

## Completed Modules (14 subsystems)

| Module | Directory | Status |
|--------|-----------|--------|
| Node Orchestrator | `agt_node/node.py` | ✅ |
| Node Identity (Ed25519) | `agt_node/identity.py` | ✅ |
| Agent Identity | `agt_node/agent_identity.py` | ✅ |
| Reputation System | `agt_node/reputation.py` | ✅ |
| Credit Wallet | `agt_node/wallet.py` | ✅ |
| Anti-Sybil | `agt_node/anti_sybil.py` | ✅ |
| Autonomous Task Generator | `agt_node/autonomous/task_generator.py` | ✅ |
| Opportunity Detector | `agt_node/autonomous/opportunity_detector.py` | ✅ |
| Agent Marketplace | `agt_node/autonomous/marketplace.py` | ✅ |
| Agent Runtime (LLM+Tools) | `agent_runtime/` | ✅ |
| P2P Network (UDP+WS) | `p2p_network/` | ✅ |
| Task Engine + Validator | `task_engine/` | ✅ |
| POI Consensus + Signatures | `poi_consensus/` | ✅ |
| Proof Registry | `poi_consensus/proof_registry.py` | ✅ |
| Impact Oracle | `impact_oracle/` | ✅ |
| Intelligence Ledger | `reward_ledger/ledger.py` | ✅ |
| Protocol Fee Engine | `reward_ledger/economy/protocol_fee.py` | ✅ |
| API Server | `api_server/server.py` | ✅ |
| Web Dashboard | `web_dashboard/` | ✅ |
| SDK | `sdk/` | ✅ |

## Frozen Components (DO NOT MODIFY)

These require a Core AIP to change:

1. `poi_consensus/intelligence_proof.py` — PoI formula
2. `agt_node/reputation.py` — Reputation model
3. `reward_ledger/ledger.py` — Ledger structure
4. `impact_oracle/scoring.py` — Impact formula
5. `impact_oracle/signals.py` — Signal weights
6. `reward_ledger/economy/protocol_fee.py` — Fee schedule + Genesis Vault
7. `agt_node/identity.py` — Ed25519 identity
8. `task_engine/validator.py` — Validator rules

## May Be Modified Without AIP

- `web_dashboard/` — UI
- `api_server/` — Additional endpoints
- `sdk/` — SDK extensions
- `examples/` — New task examples
- `scripts/` — Tooling
- `docs/` — Documentation
- Docker, CI, deployment
- Bug fixes that don't change protocol behavior
- Performance optimizations
- All test files

## Test Suite

```
269 unit tests + 16 smoke checks = 285 total checks
All passing.

Suites:
  test_agent       23 tests — LLM, Tools, Agent lifecycle
  test_api         15 tests — REST endpoints
  test_p2p         11 tests — Discovery, Connection, Protocol
  test_task        19 tests — Genesis Tasks, Dispatcher, Validator
  test_poi         48 tests — Proofs, Signatures, Ledger, Reputation
  test_identity    26 tests — Ed25519, AgentIdentity, Capabilities
  test_trust       20 tests — Registry, Traceability, Anti-Sybil
  test_impact      38 tests — Signals, Scoring, Epoch, Cycle Detection
  test_autonomous  19 tests — Opportunity Detect, Task Generate
  test_marketplace  20 tests — Marketplace, Protocol Fee, Genesis Vault
  test_simulation   15 tests — Multi-Agent, Stress, Anti-Farming
  test_e2e          9 tests — Full economic loop

Run: python -m pytest tests/ -v
Smoke: python scripts/smoke_test.py
```

## Documentation

| Document | Path | Audience |
|----------|------|----------|
| README | `/README.md` | Everyone |
| Whitepaper | `/WHITEPAPER.md` | Researchers, developers |
| Tutorial | `/docs/TUTORIAL.md` | New users |
| Audit Checklist | `/docs/AUDIT-CHECKLIST.md` | External auditors |
| Deploy Guide | `/docs/DEPLOY-VERIFY.md` | Operators |
| Roadmap | `/ROADMAP.md` | Community |
| Contributing | `/CONTRIBUTING.md` | Contributors |
| Changelog | `/CHANGELOG.md` | All |
| Security Policy | `/SECURITY.md` | Security researchers |
| Protocol Specs | `/SPECIFICATION/AGN-*.md` (8 docs) | Implementers |
| Governance | `/aip/AIP-*.md` (2 docs) | Protocol designers |
| Genesis Archive | `/genesis-archive/` (14 docs) | Historians |
| Genesis Node | `/genesis_node/` (3 docs) | Historians |

## How to Restart Work

```bash
# 1. Read this file
cat PROJECT_STATE.md

# 2. Check git state
git log --oneline -5
git status

# 3. Run smoke test
python scripts/smoke_test.py

# 4. Run full tests
python -m pytest tests/ -v

# 5. Start a node
python main.py --port 8001

# 6. Open dashboard
# http://localhost:8001
```

## Key Files to Read on Session Start

1. `PROJECT_STATE.md` (this file) — current state
2. `NEXT_SESSION.md` — what to do next
3. `README.md` — project overview
4. `SPECIFICATION/README.md` — protocol definition
5. `ROADMAP.md` — future direction
