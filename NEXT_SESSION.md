# Next Session — AGT Network

**For**: Claude or any developer resuming work on this project.
**Date**: 2026-08-01

---

## First Steps (In Order)

### 1. Read Project State
```
Read: PROJECT_STATE.md
```
This gives you the current version, architecture, frozen modules, and test status.

### 2. Verify Everything Still Works
```bash
# Smoke test (16 checks, no API key needed)
python scripts/smoke_test.py

# Full suite (269 tests)
python -m pytest tests/ -v

# Check git
git log --oneline -5
git status
```

### 3. Check GitHub
```
https://github.com/aliquanhou/AGT-Network
```
Verify: latest commits pushed, Issues enabled, Discussions enabled.

---

## What NOT to Do

### DO NOT modify these files (Protocol Frozen):
- `poi_consensus/intelligence_proof.py`
- `agt_node/reputation.py`
- `reward_ledger/ledger.py`
- `impact_oracle/scoring.py`
- `impact_oracle/signals.py`
- `reward_ledger/economy/protocol_fee.py`
- `agt_node/identity.py`
- `task_engine/validator.py`

### DO NOT add these features (→ v0.5/v1.0):
- Real token issuance
- Blockchain / on-chain deployment
- DAO governance (interface stubs exist in `reward_ledger/economy/`)
- libp2p P2P upgrade
- New economic models

### DO NOT break these rules:
- No real API keys committed
- No `.env` committed
- No private keys committed (`.pem`, `.key` → `.gitignore`)
- Clone URL must be `aliquanhou`, never `your-org`

---

## What You CAN Do

### v0.36.x Patch Work:
- [ ] Fix bugs found by external users
- [ ] Improve error messages
- [ ] Add tests for edge cases
- [ ] Improve Dashboard UI
- [ ] Add SDK examples
- [ ] Update documentation based on user feedback
- [ ] Docker improvements
- [ ] CI improvements
- [ ] Performance optimization

### External Validation Observables:
- [ ] Monitor GitHub Issues
- [ ] Monitor GitHub Stars / Forks
- [ ] Track external node deployments
- [ ] Track first community PR
- [ ] Track first third-party implementation

---

## Key Context to Remember

1. **AGT is a protocol, not a token project.** AGT Credit is experimental accounting — not cryptocurrency.

2. **Protocol Freeze is in effect.** 8 core components require Core AIPs to modify.

3. **Genesis Phase is complete.** The next milestone is external validation — not more code.

4. **27 commits, 285 checks passing.** The reference implementation is stable.

5. **Founding Team:**
   - Dr. Yu Qiuhong — Founder & Protocol Initiator
   - ChatGPT (OpenAI) — Architecture discussion, design review
   - Claude (Anthropic) — Engineering implementation
   - DeepSeek — LLM backend during development

6. **Governance**: Changes to frozen components → Draft AIP → 14-day discussion → Community review → Accept/Reject → Implement.

7. **The specification is the authority.** SPECIFICATION/AGN-*.md define the protocol. Python is the reference implementation, not the definition.

---

## Current TODO (Post-Release)

### High Priority
- [ ] Confirm repository is PUBLIC on GitHub
- [ ] Create GitHub Release v0.36.1 with release notes
- [ ] Enable GitHub Issues and Discussions
- [ ] Delete all push tokens from GitHub Settings (security)

### Medium Priority
- [ ] Monitor for first external Issues
- [ ] Respond to community questions
- [ ] Update README based on newcomer feedback

### Low Priority (v0.36.x, no protocol changes)
- [ ] Add more SDK examples
- [ ] Improve error messages for common failures
- [ ] Dashboard UI polish
- [ ] Additional Docker configurations

---

## Quick Reference

| Task | Command |
|------|---------|
| Smoke test | `python scripts/smoke_test.py` |
| Full tests | `python -m pytest tests/ -v` |
| Start node | `python main.py --port 8001` |
| Dual nodes | `python main.py --dual` |
| E2E test | `python main.py --test` |
| Docker | `docker compose up -d` |
| Dashboard | http://localhost:8001 |
| API health | http://localhost:8001/api/health |
