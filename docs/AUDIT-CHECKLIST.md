# AGT Network — External Audit Checklist

**Purpose**: For third-party reviewers evaluating AGT before its public release.
**Audience**: Developers with no prior knowledge of AGT.
**Version**: v0.36

---

## 1. Architecture Audit

- [ ] **Protocol layers are clearly separated**: Value Creation (v0.1) → Trust (v0.2) → Autonomy (v0.3). Can you trace a contribution through all three layers?
- [ ] **Data structures are the specification**: Check `IntelligenceProof`, `LedgerBlock`, `ImpactScore` — do the dataclasses define the protocol unambiguously?
- [ ] **No hidden control points**: Search codebase for `admin`, `override`, `bypass`, `emergency`. Are any of these present in protocol logic?
- [ ] **Module dependencies are acyclic**: `impact_oracle` depends on `poi_consensus`. Does `poi_consensus` depend on `impact_oracle`? (It shouldn't.)
- [ ] **Protocol constants are auditable**: Check `PROTOCOL_FEE_PCT`, `DEFAULT_MAX_SUPPLY`, `SIGNAL_WEIGHTS`. Are they constants or can they be changed at runtime?

## 2. Protocol Design Audit

- [ ] **PoI formula is internally consistent**: `Contribution = Difficulty × Quality × Verification × Innovation`. Does the code match the whitepaper?
- [ ] **Impact formula is measurable**: `Usage × Verification × Longevity × Diversity`. Are all four factors computable from on-chain data?
- [ ] **Reputation is truly soulbound**: Can reputation be transferred between agents? (Search for `score =` assignments.)
- [ ] **Supply guard is effective**: Set `max_supply = 100`, issue 90, then try to issue 20. Is it rejected?
- [ ] **Self-validation is blocked**: Try to validate your own task. Is it rejected?
- [ ] **Protocol fee is fixed**: Try to change the fee rate at runtime. Does the engine detect tampering?
- [ ] **Genesis Vault is time-locked**: Can funds be released before the vesting schedule?

## 3. Code Organization Audit

- [ ] **Directory names match protocol layers**: `agt_node/`, `agent_runtime/`, `p2p_network/` etc.
- [ ] **Tests mirror source structure**: `tests/test_poi.py` tests `poi_consensus/`, etc.
- [ ] **Archive is comprehensive**: 13 documents covering whitepaper through attack review
- [ ] **Community files present**: LICENSE, SECURITY, CoC, CHANGELOG, CONTRIBUTING
- [ ] **No dead code**: Run `pytest --cov` and check for untested critical paths

## 4. Documentation Audit

- [ ] **README: Can a stranger understand what AGT is in 60 seconds?**
- [ ] **Quick Start: Can someone clone and run in 5 minutes without reading source?**
- [ ] **Tutorial: Does `docs/TUTORIAL.md` have all steps? Is each step verifiable?**
- [ ] **API docs: Are endpoint paths and response shapes clear?**
- [ ] **Error messages: If a step fails, does the user know why and how to fix it?**
- [ ] **Genesis archive: Is the design rationale preserved? Can someone understand why decisions were made?**

## 5. Deployability Audit

- [ ] **Docker: `docker compose up` succeeds first try**
- [ ] **Windows: `start.bat` works on a clean Windows 10/11**
- [ ] **Linux: `start.sh` works on Ubuntu 22.04+**
- [ ] **macOS: `start.sh` works on macOS 14+**
- [ ] **No API key: Does the node start gracefully (with clear error message) without an API key?**
- [ ] **Wrong API key: Does the node report a useful error?**
- [ ] **Port conflict: Does the node handle port-in-use gracefully?**
- [ ] **Python version: Is Python 3.11+ enforced with a clear message?**

## 6. Security Boundary Audit

- [ ] **Private keys: Is `node_key.pem` in `.gitignore`?**
- [ ] **API keys: Is `.env` in `.gitignore`?**
- [ ] **Data directory: Are `.json` files in `data/` gitignored?**
- [ ] **Genesis Vault: Can the vault address receive direct deposits? (It should only receive via protocol fee.)**
- [ ] **Supply guard: Is `max_supply` enforced at the ledger level or can it be bypassed?**
- [ ] **Hash chain: If you manually edit `ledger_blocks.jsonl`, does `verify_chain()` detect it?**
- [ ] **Proof signatures: Can you forge a valid signature without the private key?**
- [ ] **Reputation: Can you set `rep.score = 9999` from outside the reputation module?**

## 7. Test Quality Audit

- [ ] **Coverage: Do all critical paths have tests?** (Smoke test covers the happy path. Unit tests cover edges.)
- [ ] **Boundary tests: Are max/min values tested?** (Score 0, score 1000, reputation 0, reputation 1000)
- [ ] **Tamper tests: Do tests verify that tampering is detected?** (Hash tamper, signature tamper)
- [ ] **Consensus tests: Are validator rules enforced?** (Self-validation block)
- [ ] **Stress tests: Does the system handle 500+ proofs without degradation?**

## 8. Protocol Evolution Audit

- [ ] **AIP process: Is it clear how to propose a protocol change?**
- [ ] **Protocol freeze: Is it clear which components are frozen and which are not?**
- [ ] **Versioning: Is the version consistently referenced across code and docs?**
- [ ] **Changelog: Are all versions documented with what changed and why?**

---

## Audit Verdict Template

```
Reviewer: (name)
Date: (date)
AGT Version: v0.36

Architecture:    [ ] Pass  [ ] Issues Found
Protocol Design: [ ] Pass  [ ] Issues Found
Code Quality:    [ ] Pass  [ ] Issues Found
Documentation:   [ ] Pass  [ ] Issues Found
Deployability:   [ ] Pass  [ ] Issues Found
Security:        [ ] Pass  [ ] Issues Found
Tests:           [ ] Pass  [ ] Issues Found
Governance:      [ ] Pass  [ ] Issues Found

Issues Found: (list)

Recommendation: [ ] Release Ready  [ ] Fix Before Release  [ ] Major Rework Needed
```

---

*This checklist is designed for an independent reviewer with no prior knowledge of AGT. Complete each section by following the instructions — not by asking the authors for help.*
