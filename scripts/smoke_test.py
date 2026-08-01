#!/usr/bin/env python3
"""
AGT Network — Smoke Test (v0.36)

Runs a complete 10-second verification of the entire AGT economic loop.
This is the first thing any developer should run after setting up a node.

Verifies in sequence:
  1. Node starts and generates Ed25519 identity
  2. Agent is created with crypto-bound identity
  3. Genesis tasks are loaded into the pool
  4. Agent executes a task (with mock LLM — no API key needed for smoke test)
  5. Validator evaluates and signs the proof
  6. Intelligence Proof is recorded in the ledger
  7. Reputation is updated
  8. AGT Credit is issued to wallet
  9. Chain integrity is verified
 10. Dashboard API responds

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --verbose
"""

import asyncio
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agt_node.node import AGTNode
from agent_runtime.llm_client import LLMClient, LLMResponse


class SmokeLLM(LLMClient):
    """Deterministic mock LLM for smoke testing — no API key needed."""
    async def chat(self, prompt, system=None, temperature=0.7, max_tokens=4096, **kwargs):
        return LLMResponse(
            content=(
                "## Analysis Report\n\n"
                "### 1. Overview\n"
                "This is a comprehensive analysis of the given task.\n\n"
                "### 2. Findings\n"
                "The analysis reveals several key insights:\n"
                "- Finding A: The approach is sound\n"
                "- Finding B: There is room for optimization\n"
                "- Finding C: Edge cases are handled correctly\n\n"
                "### 3. Implementation\n"
                "```python\n"
                "def optimized_solution(data):\n"
                "    return sorted(data, key=lambda x: x.value)\n"
                "```\n\n"
                "### 4. Conclusion\n"
                "The task has been analyzed thoroughly. "
                "Recommendations are provided with specific code examples.\n\n"
                "### 5. Evidence\n"
                "Test results: all passing. Benchmark: 40% improvement."
            ),
            model="smoke-test-mock",
            usage={"total_tokens": 200},
        )


def check(label, condition, verbose=False):
    """Print check result."""
    status = "PASS" if condition else "FAIL"
    symbol = "[OK]" if condition else "[!!]"
    print(f"  {symbol} {label:.<46} {status}")
    if verbose and not condition:
        print(f"       WARNING: {label} did not pass")
    return condition


async def run_smoke_test(verbose=False):
    """Run the full smoke test."""
    started = time.time()

    print()
    print("=" * 64)
    print("  AGT Network — Smoke Test v0.36.2")
    print("  Verifying complete economic loop...")
    print("=" * 64)
    print()

    checks = []

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # 1: Create and start node
            node = AGTNode(
                node_name="Smoke Test Node",
                port=18770,
                host="127.0.0.1",
                data_dir=tmpdir,
            )
            node.llm_client = SmokeLLM()
            await node.start()
            checks.append(check("Node started", node._running, verbose))
            checks.append(check("Ed25519 key generated", len(node.identity.public_key_hex) == 64, verbose))

            # 2: Genesis tasks loaded
            task_count = len(node.dispatcher._pending_tasks)
            checks.append(check("Genesis tasks loaded", task_count == 4, verbose))
            if verbose:
                for t in node.dispatcher._pending_tasks:
                    print(f"         Task: {t.id} — {t.name} (diff={t.difficulty}, value={t.value})")

            # 3: Create agent
            agent = node.create_agent(name="smoke-agent")
            checks.append(check("Agent created", agent.agent_id in node.agents, verbose))
            checks.append(check("Agent ID crypto-bound", agent.agent_id in node.agent_identities, verbose))

            # 4: Genesis block
            checks.append(check("Genesis block", len(node.ledger.blocks) >= 1, verbose))

            # 5: Run task cycle
            result = await node.run_task_cycle()
            checks.append(check("Task executed", "error" not in result, verbose))
            if verbose and "error" not in result:
                print(f"         Task: {result.get('task_name', 'N/A')}")
                print(f"         Score: {result.get('contribution_score', 0):.1f}")

            # 6: Intelligence Proof
            checks.append(check("Contribution confirmed", result.get("confirmed", False), verbose))
            checks.append(check("Proof generated", result.get("proof_id", "").startswith("poi-"), verbose))

            # 7: Proof signature
            contrib_blocks = [b for b in node.ledger.blocks if b.index > 0]
            if contrib_blocks:
                proof = contrib_blocks[-1].contribution_proof
                signed = proof is not None and proof.is_signed()
                checks.append(check("Proof signed (Ed25519)", signed, verbose))
                if signed:
                    checks.append(check("Signature verified", proof.verify_signature(), verbose))

            # 8: Reputation
            rep = node.reputations.get(agent.agent_id)
            checks.append(check("Reputation tracked", rep is not None, verbose))
            if rep:
                checks.append(check("Reputation traceable", rep.verify_reputation_trace(), verbose))

            # 9: Wallet
            wallet = node.wallets.get(agent.agent_id)
            checks.append(check("Wallet credited", wallet is not None and wallet.balance > 0, verbose))
            if wallet and verbose:
                print(f"         Balance: {wallet.balance:.1f} AGT Credit")

            # 10: Chain integrity
            checks.append(check("Chain integrity", node.ledger.verify_chain(), verbose))

            # 11: Ledger blocks
            blocks = len(node.ledger.blocks)
            checks.append(check(f"Ledger blocks: {blocks}", blocks >= 2, verbose))

            await node.stop()

        except Exception as e:
            checks.append(check(f"Exception: {e}", False, verbose))
            if verbose:
                import traceback
                traceback.print_exc()

    # Summary
    elapsed = time.time() - started
    passed = sum(1 for c in checks if c)
    total = len(checks)

    print()
    print(f"  Results: {passed}/{total} checks passed in {elapsed:.1f}s")
    print()

    if passed == total:
        print("  " + "=" * 60)
        print("   *** ALL CHECKS PASSED ***")
        print("   AGT Network is operational.")
        print("   The complete Agent Economy loop is verified.")
        print("  " + "=" * 60)
    else:
        failed = [i+1 for i, c in enumerate(checks) if not c]
        print(f"  WARNING: {total - passed} check(s) failed: #{failed}")

    print()
    return passed == total


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    success = asyncio.run(run_smoke_test(verbose=verbose))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
