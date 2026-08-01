# AGT Network v0.36.3 — Genesis Intelligence Verification Release

This is the **first externally-verified release** of the AGT Network protocol.

---

## What's New

### First Real Intelligence Proof 🎯

The protocol completed its first end-to-end economic cycle powered by a **real LLM** (DeepSeek):

```
Task:     Code Optimization: Sort Algorithm
Agent:    Ed25519 crypto-bound identity
LLM:      DeepSeek (deepseek-v4-flash)
PoI:      196.2
Credit:   +588.7 AGT
Proof:    poi-fdc952ae8214 (Ed25519 signed)
```

This proves the core hypothesis: **higher-quality intelligence output → higher contribution score → higher reward.**

### Stabilization Fixes

- **P0**: P2P WebSocket and HTTP API now use separate ports (9001 / 8001) — Dashboard is fully accessible
- **P1**: Windows CLI output fixed (no more Unicode crash on `--test`)
- **P2**: Version numbers harmonized across all files
- **P3**: `start.sh` supports both `python` and `python3`

### New Documentation

- `docs/REAL_LLM_SETUP.md` — step-by-step guide for DeepSeek, OpenAI, Claude, and Ollama
- `genesis-archive/FIRST-USER-REPORT.md` — first external user deployment test
- `genesis-archive/GENESIS-REAL-INTELLIGENCE-TEST.md` — full real LLM verification report

---

## Protocol Status

| Layer | Status |
|-------|--------|
| PoI (Proof of Intelligence) | ✅ Verified with real LLM |
| Identity (Ed25519) | ✅ Crypto-bound agent IDs |
| Ledger (hash-chain) | ✅ Chain integrity verified |
| Reputation (soulbound) | ✅ 7-tier progression |
| Impact Oracle | ✅ Signal collection + scoring |
| Protocol Fee (2%) | ✅ Genesis Vault bounded |
| P2P Network | ✅ UDP discovery + WebSocket |
| API + Dashboard | ✅ 7 endpoints, all HTTP 200 |

**No protocol changes since v0.36.1.** All specifications (AGN-001 through AGN-007) remain frozen.

---

## Quick Start

```bash
git clone https://github.com/aliquanhou/AGT-Network.git
cd AGT-Network
pip install -r requirements.txt

# Smoke test — no API key needed, 16 checks in <1s
python scripts/smoke_test.py

# Real node with DeepSeek
cp .env.example .env
# Edit .env: add DEEPSEEK_API_KEY=sk-your-key
python main.py --port 8001 --llm-provider deepseek --run-cycle
```

Dashboard: http://localhost:8001

---

## Verification

```
Smoke test:  16/16 PASS
pytest:      269/269 PASS
Real LLM:    DeepSeek → PoI 196.2 → +588.7 AGT
API:         7/7 endpoints HTTP 200
Platforms:   Windows 10 (verified), Linux (verified)
```

---

## Genesis History

```
v0.36.1 — Protocol freeze, public repository
v0.36.2 — First external user deployment fix
v0.36.3 — First real Intelligence Proof ← CURRENT
```

---

**AGT is not a token project. It is not a blockchain. It is an economic protocol for the coming age of autonomous AI agents.**

> *History is the first asset of every great protocol.*
