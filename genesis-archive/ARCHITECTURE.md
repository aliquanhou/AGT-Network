# Genesis Architecture Record

**AGT Network v0.1** — Founding Architecture
**Recorded**: 2026-08-01
**Status**: Preserved for historical reference

---

## Project Genesis Timeline

| Phase | Commit | Date | Description |
|-------|--------|------|-------------|
| Step 1 | `aa03254` | 2026-08-01 | Project scaffold: 8 modules, README, requirements |
| Step 2 | `1c65fa5` | 2026-08-01 | P2P Layer: UDP Discovery Prototype + WebSocket |
| Step 3 | `366d9cf` | 2026-08-01 | Agent Runtime: LLM + Tools + Planner + Executor |
| Step 4 | `0f58244` | 2026-08-01 | Task Engine: Genesis Tasks + Validator |
| Step 5 | `85af38e` | 2026-08-01 | POI Consensus + Intelligence Ledger + Reputation |
| Step 6 | `d32a269` | 2026-08-01 | API Server + Web Dashboard |
| Step 7 | `bb9c157` | 2026-08-01 | Node Orchestration + End-to-End Loop |
| v0.1.1 | `9ec5d81` | 2026-08-01 | Ledger Persistence + Supply Guard |
| v0.1.2 | — | 2026-08-01 | Genesis Archive (this record) |

---

## Founding Technical Decisions

### Language: Python 3.11+

Rationale: Fastest path to working prototype. LLM ecosystem maturity. No compilation step. The protocol logic is the asset, not the runtime.

### P2P: UDP Multicast (v0.1 only)

Marked as `v0.1 Discovery Prototype`. The code explicitly documents the upgrade path: `v0.5 → libp2p`, `v1.0 → AGT P2P Protocol`. This is a deliberate scaffold, not a permanent design.

### Ledger: Hash-Chained JSONL (not blockchain)

Rationale: v0.1 does not need consensus across untrusted parties. The hash chain provides tamper evidence. When the network grows to require BFT, the ledger can migrate to a proper blockchain. The data model (Intelligence Proof → Block) is designed to survive that migration.

### Storage: JSON Files

Deliberately no database. The protocol's data structures (tasks, proofs, blocks) are the specification. JSON makes the data model transparent and auditable.

### No Token Issuance

AGT Credit is explicitly labeled as experimental credit — not a real token. The `economy/` directory contains only interface stubs. This is a protocol constraint, not a missing feature.

---

## Module Map

```
AGT-Network/
├── agt_node/            Node orchestrator
│   ├── node.py          AGTNode: all subsystems integrated
│   ├── identity.py      NodeIdentity + GenesisIdentity
│   ├── reputation.py    AgentReputation: 7-tier model
│   └── wallet.py        CreditWallet: experimental accumulator
│
├── agent_runtime/       Agent execution environment
│   ├── agent.py         AGTAgent: Planner → Executor → Tools → Memory
│   ├── llm_client.py    Unified LLM: DeepSeek/OpenAI/Claude/Ollama
│   ├── planner.py       Task decomposition (LLM + fallback)
│   ├── executor.py      Step executor with tool invocation
│   └── tools.py         4 built-in tools
│
├── p2p_network/         Network layer (v0.1 UDP)
│   ├── discovery.py     UDP multicast node discovery
│   ├── connection.py    WebSocket peer connections
│   └── protocol.py      9 message types
│
├── task_engine/         Task system
│   ├── tasks.py         4 Genesis tasks + source/creator/type/value
│   ├── dispatcher.py    Assignment engine (worker≠validator rule)
│   └── validator.py     Independent Validator Agent
│
├── poi_consensus/       Proof of Intelligence
│   ├── intelligence_proof.py  Core data structure + evidence chain
│   ├── scorer.py        PoI Score computation
│   └── consensus.py     Validation → Proof → Reward pipeline
│
├── reward_ledger/       Intelligence Ledger
│   ├── ledger.py        Hash-chained blocks + persistence
│   └── economy/         Future interfaces (stubs only)
│       ├── allocation.py
│       ├── emission.py
│       └── vesting.py
│
├── api_server/          REST API
│   └── server.py        FastAPI: 12 endpoints + WebSocket
│
├── web_dashboard/       Frontend
│   ├── index.html       Single-page AGT console
│   └── app.js           Dashboard logic
│
├── tests/               120 tests (6 suites)
├── main.py              CLI entry point
└── genesis-archive/     Historical records (this directory)
```

---

## Founding Constraints (Must Not Violate)

1. **No real token issuance** → v0.1 Credit only
2. **No on-chain deployment** → Local hash chain
3. **No self-validation** → Validator != Worker
4. **No infinite rewards** → max_supply guard
5. **Genesis Identity ≠ Admin** → Historical marker only

---

*This architecture record captures the state of AGT Network at its Genesis. Future versions may diverge significantly — this document exists to preserve the original design intent.*
