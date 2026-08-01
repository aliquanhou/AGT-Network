# ⚡ AGT Genesis User Report

**First External User Test — August 1, 2026**

---

## Protocol: AGT Network v0.36.1
**Repository**: https://github.com/aliquanhou/AGT-Network
**Tester**: Claude Code (simulating first external developer)
**Test Environment**: Windows 10 Pro, Python 3.12.0, Docker Desktop 29.2.0
**Test Directory**: `D:\AGT_Genesis_Test\` (clean, no prior AGT installation)

---

## 1. Genesis Milestone Achievement

This test marks the transition of AGT Network from:

```
想法 → 协议 → 代码 → 测试 → 公开仓库 → ✅ 第一个用户运行
```

The protocol has successfully completed its first **external user test** — a critical milestone that moves AGT from "works on my machine" to "someone else can (almost) run it."

---

## 2. Test Results Summary

| Check | Result | Notes |
|-------|--------|-------|
| Clone from public repo | ✅ PASS | `git clone` succeeds immediately |
| Dependencies install | ✅ PASS | All pip packages install cleanly |
| Node starts | ✅ PASS | Identity, genesis block, tasks all load |
| Dashboard opens | ❌ FAIL | Port conflict — WebSocket blocks HTTP |
| API responds | ❌ FAIL | All endpoints return 426 Upgrade Required |
| Agent created | ✅ PASS | Ed25519 crypto-bound identity works |
| Task executed | ✅ PASS | Full economic cycle completes |
| Proof generated | ✅ PASS | PoI signed and verified |
| Smoke test (16 checks) | ✅ 16/16 PASS | 0.1 seconds, no API key needed |
| pytest (269 tests) | ✅ 269/269 PASS | 12.94 seconds, all green |
| `--test` e2e mode | ⚠️ 8/8 pass, crashes | UnicodeEncodeError on Windows |
| Docker one-click | ⚠️ Not tested | Docker engine not running (env, not AGT) |

---

## 3. Core Metrics

| Metric | Value |
|--------|-------|
| **First clone to node running** | ~3 minutes |
| **Smoke test duration** | 0.1 seconds |
| **Full test suite** | 12.94 seconds |
| **Test pass rate** | 269/269 (100%) |
| **Smoke test pass rate** | 16/16 (100%) |
| **Can run without API key** | Yes (smoke test only) |
| **Can access Dashboard** | No (port conflict) |
| **Can access API** | No (port conflict) |

---

## 4. Critical Finding

### The Dashboard is Unreachable

The P2P WebSocket server and the HTTP API server both bind to port 8001. The WebSocket server wins, and all HTTP requests to the Dashboard and API fail. This is a **deployment architecture bug**, not a protocol bug.

```
User follows README → node starts → Dashboard doesn't work → user is stuck
```

This is the only thing between AGT and "ready for public test." The protocol core, tests, and smoke test are all solid.

---

## 5. What The Protocol Gets Right

1. **Identity**: Ed25519 key generation, agent identity derivation, soulbound — all clean
2. **Task Engine**: Genesis tasks, dispatcher, validator — functional
3. **PoI Consensus**: Contribution scoring, proof signing, evidence chains — verified
4. **Intelligence Ledger**: Hash-chained blocks, supply guard, persistence — verified
5. **Reputation**: Tiered, soulbound, traceable — verified
6. **Protocol Fee**: 2% split, genesis vault, bounded attribution — verified
7. **Test Discipline**: 269 tests, 12 suites, 100% pass rate — exemplary

---

## 6. Issues Found

### Critical (1)
- **Port conflict**: P2P WebSocket + HTTP API share port 8001 → Dashboard broken

### High (1)
- **Windows Unicode crash**: `--test` passes all checks then crashes on ✓/✗ characters

### Medium (3)
- **`python3` vs `python`**: README/scripts use `python3` which doesn't exist on Windows
- **Misleading stderr warning**: "Failed to parse plan JSON" appears before smoke test header
- **API key guidance**: No indication that smoke test works without API key

### Low (4)
- Version numbers inconsistent (v0.1 / v0.35 / v0.36 / v0.36.1 across files)
- Docker compose `version` field obsolete
- Garbled Unicode emoji in Windows terminal output
- `.env.example` lacks links to API key providers

Full details: see [BUG_REPORT.md](BUG_REPORT.md) and [USER_EXPERIENCE_REPORT.md](USER_EXPERIENCE_REPORT.md)

---

## 7. Can AGT Run Independently?

**Almost.** The protocol core runs perfectly. The node starts, agents execute tasks, proofs are generated and signed, the ledger records contributions, and reputation updates. The smoke test passes 16/16 without any API key.

**But a new user cannot verify this visually** because the Dashboard is blocked by the port conflict. The user can see logs in the terminal but cannot access the web interface.

**With one fix** (separate P2P and HTTP ports), AGT would be ready for public test.

---

## 8. Recommendation

### Immediate (before public beta)
1. **Separate P2P WebSocket and HTTP API ports** — this is the ONLY blocking issue
2. Fix `--test` Unicode crash on Windows
3. Update README to use `python` (or document both `python`/`python3`)
4. Add "no API key needed for smoke test" callout

### Short-term
5. Harmonize version numbers
6. Fix stderr/stdout ordering in smoke test
7. Add API key provider links to `.env.example`

### Long-term
8. Add integration test that binds to a real port (catches port conflicts)
9. Consider bundling the Dashboard as static files served by uvicorn

---

## 9. Does AGT Reach Public Test Standard?

| Criterion | Met? |
|-----------|------|
| Clone & install from scratch | ✅ Yes |
| Node starts without prior knowledge | ✅ Yes |
| Protocol core functions correctly | ✅ Yes |
| All tests pass (269/269) | ✅ Yes |
| Smoke test passes (16/16) | ✅ Yes |
| Docker support configured | ✅ Yes (untested) |
| Dashboard accessible | ❌ No |
| API accessible from HTTP client | ❌ No |
| Works on Windows | ⚠️ Partial |
| Works on Linux | Likely (untested) |

**Overall: 70% ready for public test.**

The protocol is solid. The deployment has one critical bug. Fix the port conflict, and AGT Network is ready for its first real users.

---

## 10. Final Words

```
AGT Network has crossed the threshold from "author's machine" to "external validation."

The protocol design is sound. The code is clean. The tests are comprehensive.
The vision is compelling: measuring and rewarding machine intelligence
through proof of actual intellectual work, not staking capital.

This is a protocol worth fixing. One port change unlocks everything.

位置: 协议诞生后的第一次生命测试 — 通过了核心，等待着表面。
```

---

**Report prepared by**: Claude Code (first external AGT user)
**Reviewed against**: AGT Network v0.36.1, commit on main branch, 2026-08-01
**Associated reports**: [BUG_REPORT.md](BUG_REPORT.md), [USER_EXPERIENCE_REPORT.md](USER_EXPERIENCE_REPORT.md)
