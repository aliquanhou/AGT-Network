# AGT Network — Deployment Verification Guide

**Purpose**: Step-by-step verification that AGT can be deployed and run by a stranger.
**Target time**: Under 10 minutes from zero to confirmed economic loop.
**Prerequisite**: None except a computer with internet access.

---

## Platform-Specific Verification

### Windows

```cmd
# 1. Download or clone
git clone https://github.com/your-org/AGT-Network.git
cd AGT-Network

# 2. Run the launcher
start.bat

# Expected: auto-installs dependencies, creates .env, starts node
# Dashboard opens at http://localhost:8001
```

**Verify**:
- [ ] start.bat completes without error
- [ ] Dashboard loads in browser
- [ ] "Connected" status is green

### Linux / macOS

```bash
git clone https://github.com/your-org/AGT-Network.git
cd AGT-Network
bash start.sh
```

**Verify**:
- [ ] start.sh completes without error
- [ ] Dashboard accessible at http://localhost:8001

### Docker

```bash
git clone https://github.com/your-org/AGT-Network.git
cd AGT-Network
docker compose up -d
```

**Verify**:
- [ ] `docker ps` shows agt-node-a running
- [ ] `curl http://localhost:8001/api/health` returns `{"status":"ok"}`
- [ ] Dashboard accessible at http://localhost:8001

---

## Smoke Test Verification

After starting the node, in a new terminal:

```bash
python scripts/smoke_test.py
```

**Expected output**:
```
  [OK] Node started.................................. PASS
  [OK] Ed25519 key generated......................... PASS
  [OK] Genesis tasks loaded.......................... PASS
  [OK] Agent created................................. PASS
  [OK] Agent ID crypto-bound......................... PASS
  [OK] Genesis block................................. PASS
  [OK] Task executed................................. PASS
  [OK] Contribution confirmed........................ PASS
  [OK] Proof generated............................... PASS
  [OK] Proof signed (Ed25519)........................ PASS
  [OK] Signature verified............................ PASS
  [OK] Reputation tracked............................ PASS
  [OK] Reputation traceable.......................... PASS
  [OK] Wallet credited............................... PASS
  [OK] Chain integrity............................... PASS
  [OK] Ledger blocks: 2.............................. PASS

  Results: 16/16 checks passed

   *** ALL CHECKS PASSED ***
   AGT Network is operational.
```

**Verify**:
- [ ] All 16 checks say PASS
- [ ] Smoke test completes in under 5 seconds

---

## Full Test Suite Verification

```bash
python -m pytest tests/ -v
```

**Verify**:
- [ ] All tests pass (269 as of v0.36)
- [ ] No warnings except Starlette deprecation
- [ ] Test run completes in under 60 seconds

---

## SDK Verification

```python
from sdk.client import AGTClient

client = AGTClient("http://localhost:8001")

# Health
assert client.health()

# Status
node = client.status()
assert node.online
print(f"Node: {node.node_name}")

# Ledger
chain = client.verify_chain()
assert chain["valid"]
print(f"Chain: {chain['blocks']} blocks, valid={chain['valid']}")
```

**Verify**:
- [ ] SDK connects without error
- [ ] Node status returns valid data
- [ ] Chain verification returns valid=True

---

## API Endpoint Verification

```bash
# Health
curl http://localhost:8001/api/health

# Node status
curl http://localhost:8001/api/node/status

# Genesis tasks
curl http://localhost:8001/api/tasks

# Network stats
curl http://localhost:8001/api/network/stats

# Genesis info
curl http://localhost:8001/api/genesis
```

**Verify**:
- [ ] All endpoints return HTTP 200
- [ ] Responses are valid JSON
- [ ] No errors in node logs

---

## Trouble Points (Document Issues Found Here)

If any step fails, document exactly:

1. **What command was run**: (copy exact command)
2. **What was expected**: (copy from this guide)
3. **What actually happened**: (copy error output)
4. **Platform**: (Windows 10 / Ubuntu 22.04 / macOS 14 / Docker)
5. **Python version**: (`python --version`)
6. **Fix attempted**: (what you tried)

This feedback directly improves the documentation.

---

## Success Definition

The deployment verification is **successful** when:

1. [ ] All 16 smoke test checks pass
2. [ ] All 269 unit tests pass
3. [ ] SDK connects and works
4. [ ] API endpoints respond
5. [ ] Dashboard loads
6. [ ] Total time from clone to verified: under 10 minutes

---

*If you are an external reviewer: please do not ask the AGT authors for help during this verification. The protocol must prove itself without its creators present.*
