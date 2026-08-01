"""
Tests: End-to-End — AGT Genesis Prototype Full Loop

Verifies the complete economic cycle end-to-end:
    Agent → Task → Execute → Validate →
    Intelligence Proof → Reputation → Ledger → AGT Credit

This is the defining test for AGT Network v0.1.
"""

import asyncio
import os
import pytest
import tempfile
from unittest.mock import MagicMock

from agt_node.node import AGTNode
from agent_runtime.agent import AGTAgent
from agent_runtime.llm_client import LLMClient, LLMResponse
from task_engine.tasks import get_task_by_id
from poi_consensus.intelligence_proof import IntelligenceProof
from reward_ledger.ledger import IntelligenceLedger
from agt_node.reputation import AgentReputation, DEFAULT_REPUTATION


# ============================================================
# Mock LLM for deterministic e2e testing
# ============================================================

class E2EMockLLM(LLMClient):
    """Mock LLM that returns high-quality responses for e2e testing"""
    async def chat(self, prompt, system=None, temperature=0.7, max_tokens=4096, **kwargs):
        return LLMResponse(
            content=(
                "## Comprehensive Analysis\n\n"
                "This is a detailed response to the task.\n\n"
                "### Section 1: Overview\n"
                "The task requires careful analysis and creative problem-solving.\n\n"
                "### Section 2: Implementation\n"
                "```python\n"
                "def solution():\n"
                "    return 'optimized result'\n"
                "```\n\n"
                "### Section 3: Analysis\n"
                "An interesting insight is that this approach yields significant improvements.\n\n"
                "### Section 4: Conclusion\n"
                "The solution meets all requirements with high quality.\n\n"
                "## Examples\n"
                "- Example 1: demonstrates the approach\n"
                "- Example 2: shows edge case handling\n"
                "- Example 3: validates performance\n"
            ) * 2,
            model="mock-e2e",
            usage={"total_tokens": 500},
        )


# ============================================================
# E2E Tests
# ============================================================

class TestE2EEconomicLoop:
    """Full economic loop verification"""

    @pytest.mark.asyncio
    async def test_complete_cycle(self):
        """
        E2E TEST: Complete AGT economic cycle

        Verifies all 8 steps of the AGT Genesis loop:
          1. Task created (Genesis task)
          2. Agent executes task
          3. Validator validates result
          4. Intelligence Proof generated
          5. Reputation updated
          6. Intelligence Ledger recorded
          7. AGT Credit issued
          8. Wallet credited
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            node = AGTNode(
                node_name="E2E Test Node",
                port=19981,
                host="127.0.0.1",
                data_dir=tmpdir,
            )

            # Inject mock LLM
            node.llm_client = E2EMockLLM()

            await node.start()

            assert node._running
            assert len(node.dispatcher._pending_tasks) == 4  # 4 Genesis tasks

            # ---- Step 1: Create Agent ----
            agent = node.create_agent(name="e2e-agent")
            assert agent.agent_id in node.agents
            assert agent.agent_id in node.wallets
            assert agent.agent_id in node.reputations

            # ---- Step 2: Run task cycle ----
            result = await node.run_task_cycle()

            # ---- Step 3: Verify execution ----
            assert "error" not in result, f"Cycle failed: {result.get('error')}"
            assert result["execution_success"], "Task execution should succeed"
            assert result["confirmed"], "Contribution should be confirmed"

            # ---- Step 4: Verify Intelligence Proof ----
            assert result["proof_id"].startswith("poi-")
            assert result["contribution_score"] > 0

            # ---- Step 5: Verify Reputation ----
            rep = node.reputations[agent.agent_id]
            assert rep.score != DEFAULT_REPUTATION, (
                f"Reputation should have changed from {DEFAULT_REPUTATION}"
            )
            assert len(rep.history) >= 1

            # ---- Step 6: Verify Ledger ----
            assert node.ledger.total_contributions >= 2  # Genesis + contribution
            # At least one block is a non-genesis contribution
            contrib_blocks = [b for b in node.ledger.blocks if b.index > 0]
            assert len(contrib_blocks) >= 1

            # ---- Step 7: Verify AGT Credit ----
            total_reward = sum(b.reward_credit for b in contrib_blocks)
            assert total_reward > 0, "Should have issued AGT Credit"

            # ---- Step 8: Verify Wallet ----
            wallet = node.wallets[agent.agent_id]
            assert wallet.balance > 0, "Wallet should have received AGT Credit"

            # ---- Verify chain integrity ----
            assert node.ledger.verify_chain(), "Ledger chain should be intact"

            await node.stop()

    @pytest.mark.asyncio
    async def test_multiple_cycles(self):
        """Run multiple task cycles and verify accumulation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            node = AGTNode(
                node_name="Multi-Cycle Test",
                port=19982,
                host="127.0.0.1",
                data_dir=tmpdir,
            )
            node.llm_client = E2EMockLLM()
            await node.start()

            agent = node.create_agent(name="multi-agent")

            # Run 2 cycles
            result1 = await node.run_task_cycle()
            result2 = await node.run_task_cycle()

            assert result1["confirmed"]
            assert result2["confirmed"]

            # Reputation should have changed twice
            rep = node.reputations[agent.agent_id]
            assert len(rep.history) >= 2

            # Wallet accumulated
            wallet = node.wallets[agent.agent_id]
            assert wallet.balance >= result1["reward_credit"] + result2["reward_credit"]

            # Ledger has multiple contribution blocks
            contrib_blocks = [b for b in node.ledger.blocks if b.index > 0]
            assert len(contrib_blocks) >= 2

            assert node.ledger.verify_chain()

            await node.stop()

    @pytest.mark.asyncio
    async def test_genesis_identity_preserved(self):
        """Genesis identity is created and immutable"""
        with tempfile.TemporaryDirectory() as tmpdir:
            node = AGTNode(
                node_name="Genesis Test",
                port=19983,
                host="127.0.0.1",
                founder_id="Dr. Yu Qiuhong",
                data_dir=tmpdir,
            )
            node.llm_client = E2EMockLLM()
            await node.start()

            assert node.genesis_identity is not None
            assert node.genesis_identity.founder_id == "Dr. Yu Qiuhong"
            assert node.genesis_identity.version.startswith("v0.")
            assert len(node.genesis_identity.genesis_hash) == 64

            # Genesis identity is a record, not a privilege
            d = node.genesis_identity.to_dict()
            assert "admin" not in str(d).lower()
            assert "privilege" not in str(d).lower()

            await node.stop()

    @pytest.mark.asyncio
    async def test_e2e_dual_node_simulation(self):
        """
        Simulate two nodes: one executes tasks, both produce contributions.

        This validates the multi-node scenario described in the task spec:
          "Two computers running two AGT Nodes, agents can discover each other"
        """
        with tempfile.TemporaryDirectory() as tmpdir_a, tempfile.TemporaryDirectory() as tmpdir_b:
            node_a = AGTNode(
                node_name="Node A",
                port=19984,
                host="127.0.0.1",
                data_dir=tmpdir_a,
            )
            node_a.llm_client = E2EMockLLM()

            node_b = AGTNode(
                node_name="Node B",
                port=19985,
                host="127.0.0.1",
                data_dir=tmpdir_b,
            )
            node_b.llm_client = E2EMockLLM()

            await node_a.start()
            await node_b.start()

            # Connect nodes to each other
            await node_a.connection.connect_to_peer(node_b.node_id, "127.0.0.1", 19985)

            # Create agents on each
            agent_a = node_a.create_agent(name="worker-a")
            agent_b = node_b.create_agent(name="worker-b")

            # Run cycles on both nodes
            result_a = await node_a.run_task_cycle()
            result_b = await node_b.run_task_cycle()

            # Both should produce contributions
            assert result_a["confirmed"], "Node A cycle should succeed"
            assert result_b["confirmed"], "Node B cycle should succeed"

            # Both have ledger entries
            assert node_a.ledger.total_contributions >= 2
            assert node_b.ledger.total_contributions >= 2

            # Both chains intact
            assert node_a.ledger.verify_chain()
            assert node_b.ledger.verify_chain()

            # Both nodes have wallets with credit
            wallet_a = node_a.wallets[agent_a.agent_id]
            wallet_b = node_b.wallets[agent_b.agent_id]
            assert wallet_a.balance > 0
            assert wallet_b.balance > 0

            await node_a.stop()
            await node_b.stop()

    @pytest.mark.asyncio
    async def test_evidence_chain_in_proof(self):
        """Each contribution proof contains a verifiable evidence chain"""
        with tempfile.TemporaryDirectory() as tmpdir:
            node = AGTNode(
                node_name="Evidence Test",
                port=19986,
                host="127.0.0.1",
                data_dir=tmpdir,
            )
            node.llm_client = E2EMockLLM()
            await node.start()
            node.create_agent(name="evidence-agent")

            result = await node.run_task_cycle()

            # Find the proof in the ledger
            contrib_blocks = [b for b in node.ledger.blocks if b.index > 0]
            assert len(contrib_blocks) >= 1

            proof = contrib_blocks[0].contribution_proof
            assert proof is not None

            # Evidence chain
            assert len(proof.evidence) >= 3  # artifact + validation + benchmark
            evidence_types = {e.type for e in proof.evidence}
            assert "artifact_hash" in evidence_types or "validation_feedback" in evidence_types

            # Proof hash is verifiable
            h = proof.compute_hash()
            assert len(h) == 64

            await node.stop()

    @pytest.mark.asyncio
    async def test_reputation_affects_display(self):
        """Reputation changes are visible in agent status"""
        with tempfile.TemporaryDirectory() as tmpdir:
            node = AGTNode(
                node_name="Rep Display Test",
                port=19987,
                host="127.0.0.1",
                data_dir=tmpdir,
            )
            node.llm_client = E2EMockLLM()
            await node.start()
            agent = node.create_agent(name="rep-agent")

            # Initial reputation
            rep = node.reputations[agent.agent_id]
            initial_score = rep.score
            initial_level = rep.level

            # Run a high-quality cycle
            await node.run_task_cycle()

            # Reputation should be reflected
            assert rep.score != initial_score or rep.level != initial_level

            # Agent status includes reputation
            status = agent.status()
            assert "tasks_completed" in status
            assert status["tasks_completed"] >= 1

            await node.stop()
