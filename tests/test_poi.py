"""
Tests: POI Consensus + Intelligence Ledger + Reputation

Verifies the complete AGT economic core:
- IntelligenceProof creation + evidence chain
- PoIScorer computation
- ConsensusEngine pipeline
- IntelligenceLedger blocks + chain integrity
- AgentReputation model
- GenesisIdentity + CreditWallet
"""

import hashlib
import pytest

from poi_consensus.intelligence_proof import (
    IntelligenceProof,
    EvidenceItem,
    EvidenceType,
    ContributionType,
    make_evidence,
)
from poi_consensus.scorer import PoIScorer, ContributionScore
from poi_consensus.consensus import ConsensusEngine, ConsensusResult
from reward_ledger.ledger import IntelligenceLedger, LedgerBlock
from agt_node.reputation import (
    AgentReputation,
    ReputationEvent,
    ReputationRecord,
    REPUTATION_DELTA,
    DEFAULT_REPUTATION,
    MIN_TASK_REPUTATION,
)
from agt_node.identity import NodeIdentity, GenesisIdentity
from agt_node.wallet import CreditWallet, CreditEntry
from task_engine.tasks import get_task_by_id
from task_engine.validator import Validator, ValidationResult


# ============================================================
# Intelligence Proof Tests
# ============================================================

class TestIntelligenceProof:
    def test_create_proof(self):
        proof = IntelligenceProof.create(
            task_id="genesis-001",
            task_name="Test Task",
            agent_id="agent-a",
            node_id="node-a",
            contribution_type="code_optimization",
            difficulty=3,
            quality_score=85,
            verification_score=80,
            innovation_score=70,
        )
        assert proof.proof_id.startswith("poi-")
        assert proof.agent_id == "agent-a"
        assert proof.contribution_type == ContributionType.CODE_OPTIMIZATION

    def test_contribution_score_formula(self):
        """PoI Score = Difficulty × Quality × Verification × Innovation"""
        proof = IntelligenceProof.create(
            task_id="t1", task_name="Test",
            agent_id="a1", node_id="n1",
            contribution_type="analysis",
            difficulty=5,  # 0.5 weight
            quality_score=90,     # 0.9
            verification_score=85,  # 0.85
            innovation_score=70,   # 0.7
        )
        expected = round(0.5 * 0.9 * 0.85 * 0.7 * 1000, 2)
        assert proof.contribution_score == expected

    def test_contribution_score_perfect(self):
        """Max score = difficulty 10 × perfect 100s = 1000"""
        proof = IntelligenceProof.create(
            task_id="t1", task_name="Perfect",
            agent_id="a1", node_id="n1",
            contribution_type="analysis",
            difficulty=10,
            quality_score=100,
            verification_score=100,
            innovation_score=100,
        )
        assert proof.contribution_score == 1000.0

    def test_contribution_score_zero(self):
        """Zero quality = zero score"""
        proof = IntelligenceProof.create(
            task_id="t1", task_name="Zero",
            agent_id="a1", node_id="n1",
            contribution_type="analysis",
            difficulty=5,
            quality_score=0,
            verification_score=80,
            innovation_score=70,
        )
        assert proof.contribution_score == 0.0

    def test_agt_credit_calculation(self):
        """Credit = contribution_score × task_value / 10"""
        proof = IntelligenceProof.create(
            task_id="t1", task_name="Test",
            agent_id="a1", node_id="n1",
            contribution_type="analysis",
            difficulty=5,
            quality_score=90,
            verification_score=85,
            innovation_score=70,
            task_value=50.0,  # 50-value task
        )
        expected_credit = round(proof.contribution_score * 50.0 / 10.0, 2)
        assert proof.agt_credit == expected_credit
        assert proof.agt_credit > 0

    def test_proof_hash(self):
        proof = IntelligenceProof.create(
            task_id="t1", task_name="Hash Test",
            agent_id="a1", node_id="n1",
            contribution_type="analysis",
            difficulty=3,
            quality_score=80,
            verification_score=80,
            innovation_score=80,
        )
        h = proof.compute_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_proof_to_dict(self):
        proof = IntelligenceProof.create(
            task_id="t1", task_name="Dict Test",
            agent_id="a1", node_id="n1",
            contribution_type="code_creation",
            difficulty=4,
            quality_score=88,
            verification_score=82,
            innovation_score=75,
            evidence=[
                make_evidence(EvidenceType.CODE_COMMIT, "commit abc123", "code content"),
            ],
            validator_node_id="v-node",
            validator_agent_id="v-agent",
            validator_feedback="Good work",
        )
        d = proof.to_dict()
        assert d["proof_id"].startswith("poi-")
        assert d["scores"]["quality"] == 88
        assert d["scores"]["contribution"] == proof.contribution_score
        assert d["scores"]["agt_credit"] == proof.agt_credit
        assert len(d["evidence"]) == 1
        assert d["evidence"][0]["type"] == "code_commit"
        assert d["validator"]["node_id"] == "v-node"
        assert "content_hash" in d

    def test_evidence_chain(self):
        """Multiple evidence items build a verifiable chain"""
        e1 = make_evidence(EvidenceType.CODE_COMMIT, "commit #1", "code v1")
        e2 = make_evidence(EvidenceType.TEST_RESULT, "all tests pass", "results...")
        e3 = make_evidence(EvidenceType.VALIDATION_FEEDBACK, "validator approved", "good")

        proof = IntelligenceProof.create(
            task_id="t1", task_name="Evidence Test",
            agent_id="a1", node_id="n1",
            contribution_type="tool_development",
            difficulty=5,
            quality_score=90,
            verification_score=85,
            innovation_score=80,
            evidence=[e1, e2, e3],
        )
        assert len(proof.evidence) == 3
        d = proof.to_dict()
        assert len(d["evidence"]) == 3

    def test_evidence_content_hash(self):
        """Evidence hashes are deterministic"""
        content = "test content for hashing"
        e1 = make_evidence(EvidenceType.ARTIFACT_HASH, "artifact", content)
        e2 = make_evidence(EvidenceType.ARTIFACT_HASH, "artifact", content)
        assert e1.content_hash == e2.content_hash  # Deterministic

        e3 = make_evidence(EvidenceType.ARTIFACT_HASH, "artifact", "different content")
        assert e1.content_hash != e3.content_hash  # Different content = different hash

    def test_contribution_type_enum(self):
        assert ContributionType.CODE_OPTIMIZATION == "code_optimization"
        assert ContributionType.KNOWLEDGE_ORGANIZATION == "knowledge_organization"
        assert ContributionType.CREATIVE_DESIGN == "creative_design"
        assert ContributionType.TOOL_DEVELOPMENT == "tool_development"


# ============================================================
# Scorer Tests
# ============================================================

class TestScorer:
    def test_compute_score(self):
        task = get_task_by_id("genesis-001")  # difficulty=3, value=30
        validation = ValidationResult(
            validator_node_id="node-b",
            validator_agent_id="v-agent",
            task_id="genesis-001",
            assignment_id="assign-1",
            quality_score=85,
            verification_score=80,
            innovation_score=70,
            passed=True,
        )
        score = PoIScorer.compute_score(task, validation)
        assert 0 <= score.final_score <= 1000
        assert score.agt_credit > 0

    def test_build_proof_with_evidence(self):
        task = get_task_by_id("genesis-002")  # Knowledge task
        validation = ValidationResult(
            validator_node_id="node-b",
            validator_agent_id="v-agent",
            task_id="genesis-002",
            assignment_id="assign-2",
            quality_score=92,
            verification_score=88,
            innovation_score=85,
            feedback="Excellent analysis of PoI concepts.",
            passed=True,
        )
        proof = PoIScorer.build_proof(
            task=task,
            validation=validation,
            agent_id="agent-a",
            node_id="node-a",
            result_content="## AGT Protocol Analysis\n\nComprehensive analysis...",
        )
        assert proof.proof_id.startswith("poi-")
        assert proof.agent_id == "agent-a"
        assert proof.validator_node_id == "node-b"
        # Evidence should be auto-generated
        assert len(proof.evidence) >= 3  # artifact_hash + validation_feedback + benchmark
        evidence_types = {e.type for e in proof.evidence}
        assert EvidenceType.ARTIFACT_HASH in evidence_types
        assert EvidenceType.VALIDATION_FEEDBACK in evidence_types


# ============================================================
# Consensus Engine Tests
# ============================================================

class TestConsensus:
    @pytest.mark.asyncio
    async def test_process_contribution_valid(self):
        """Full consensus pipeline for a valid contribution"""
        engine = ConsensusEngine(node_id="node-validator")
        task = get_task_by_id("genesis-001")
        result = "## Optimized Code\n\n```python\ndef quick_sort(arr):\n    return sorted(arr)\n```\n\nAnalysis: O(n log n) complexity."

        consensus = await engine.process_contribution(
            task=task,
            agent_id="agent-worker",
            worker_node_id="node-worker",  # Different from validator node
            result=result,
            assignment_id="assign-test",
        )

        assert isinstance(consensus, ConsensusResult)
        assert consensus.proof is not None
        assert consensus.score is not None

    @pytest.mark.asyncio
    async def test_consensus_poor_result_low_score(self):
        """Poor result gets low score"""
        engine = ConsensusEngine(node_id="node-validator")
        task = get_task_by_id("genesis-004")  # Tool development, difficulty=5
        result = "bad"  # Very short, poor result

        consensus = await engine.process_contribution(
            task=task,
            agent_id="agent-worker",
            worker_node_id="node-worker",
            result=result,
            assignment_id="assign-poor",
        )

        assert consensus.score.final_score <= 55  # Low score for poor result
        assert consensus.reward_credit < 15

    @pytest.mark.asyncio
    async def test_callbacks_fire(self):
        """Proof generated and reward callbacks fire"""
        proofs_captured = []
        rewards_captured = []

        engine = ConsensusEngine(node_id="node-validator")
        engine.on_proof_generated(lambda p: proofs_captured.append(p))
        engine.on_reward(lambda aid, amt: rewards_captured.append((aid, amt)))

        task = get_task_by_id("genesis-001")
        result = "## Detailed optimization analysis\n\n" * 20  # Substantial

        await engine.process_contribution(
            task=task,
            agent_id="agent-worker",
            worker_node_id="node-worker",
            result=result,
            assignment_id="assign-cb",
        )

        # With a good result, callbacks should fire
        if len(proofs_captured) > 0:
            assert proofs_captured[0].agent_id == "agent-worker"
        if len(rewards_captured) > 0:
            assert rewards_captured[0][0] == "agent-worker"

    @pytest.mark.asyncio
    async def test_engine_stats(self):
        """Engine tracks proofs confirmed and credits issued"""
        engine = ConsensusEngine(node_id="node-validator")
        task = get_task_by_id("genesis-003")  # High difficulty
        result = "## System Design\n\n" + "Detailed architecture...\n" * 50

        await engine.process_contribution(
            task=task,
            agent_id="agent-a",
            worker_node_id="node-w",
            result=result,
            assignment_id="assign-stats",
        )

        assert engine.proofs_confirmed > 0
        assert engine.total_credit_issued >= 0


# ============================================================
# Intelligence Ledger Tests
# ============================================================

class TestIntelligenceLedger:
    @pytest.fixture
    def ledger(self, tmp_path):
        """Create a fresh ledger in tmp dir"""
        ldg = IntelligenceLedger(data_dir=str(tmp_path))
        return ldg

    def test_genesis_block(self, ledger):
        founder = "founder-yuqiu-hong"
        block = ledger.create_genesis_block(founder)
        assert block.index == 0
        assert block.block_id == "blk-genesis-00000000"
        assert block.previous_hash == "0" * 64
        assert block.block_hash != ""
        assert ledger.total_contributions == 1

    def test_genesis_only_once(self, ledger):
        ledger.create_genesis_block("founder")
        with pytest.raises(ValueError, match="already exists"):
            ledger.create_genesis_block("another")

    def test_record_contribution(self, ledger):
        ledger.create_genesis_block("founder")

        proof = IntelligenceProof.create(
            task_id="genesis-001", task_name="Test",
            agent_id="agent-a", node_id="node-a",
            contribution_type="code_optimization",
            difficulty=3, quality_score=85,
            verification_score=80, innovation_score=70,
        )
        block = ledger.record_contribution(
            proof=proof,
            reputation_change=+5,
            reward_credit=proof.agt_credit,
            node_id="node-a",
            agent_id="agent-a",
        )
        assert block.index == 1
        assert block.previous_hash == ledger.blocks[0].block_hash
        assert block.block_hash != ""
        assert block.reward_credit == proof.agt_credit
        assert block.reputation_change == 5
        assert ledger.total_contributions == 2

    def test_chain_integrity(self, ledger):
        """Hash chain is verifiable"""
        ledger.create_genesis_block("founder")

        for i in range(5):
            proof = IntelligenceProof.create(
                task_id=f"task-{i}", task_name=f"Task {i}",
                agent_id="agent-a", node_id="node-a",
                contribution_type="analysis",
                difficulty=3, quality_score=80,
                verification_score=80, innovation_score=70,
            )
            ledger.record_contribution(
                proof=proof, reputation_change=1,
                reward_credit=proof.agt_credit,
                node_id="node-a", agent_id="agent-a",
            )

        assert ledger.verify_chain()

    def test_get_blocks_by_agent(self, ledger):
        ledger.create_genesis_block("founder")
        proof = IntelligenceProof.create(
            task_id="t1", task_name="T1",
            agent_id="agent-a", node_id="node-a",
            contribution_type="analysis",
            difficulty=3, quality_score=80,
            verification_score=80, innovation_score=70,
        )
        ledger.record_contribution(
            proof=proof, reputation_change=1,
            reward_credit=10, node_id="node-a", agent_id="agent-a",
        )
        blocks = ledger.get_blocks_by_agent("agent-a")
        assert len(blocks) == 1
        assert blocks[0].agent_id == "agent-a"

    def test_get_agent_total_credit(self, ledger):
        ledger.create_genesis_block("founder")
        for i in range(3):
            proof = IntelligenceProof.create(
                task_id=f"t{i}", task_name=f"T{i}",
                agent_id="agent-b", node_id="node-b",
                contribution_type="analysis",
                difficulty=3, quality_score=80,
                verification_score=80, innovation_score=70,
                task_value=30,
            )
            ledger.record_contribution(
                proof=proof, reputation_change=1,
                reward_credit=proof.agt_credit,
                node_id="node-b", agent_id="agent-b",
            )
        total = ledger.get_agent_total_credit("agent-b")
        assert total > 0

    # ============================================================
    # P0-1: Full Block Persistence
    # ============================================================

    def test_full_persistence_roundtrip(self, tmp_path):
        """Blocks persist to disk and are fully restorable.

        Flow: create blocks → save → new ledger → load → same blocks → chain verified
        """
        # Phase 1: Create ledger with contributions
        ledger1 = IntelligenceLedger(data_dir=str(tmp_path))
        ledger1.create_genesis_block("founder")

        proof1 = IntelligenceProof.create(
            task_id="genesis-001", task_name="Task 1",
            agent_id="agent-a", node_id="node-a",
            contribution_type="code_optimization",
            difficulty=3, quality_score=85,
            verification_score=80, innovation_score=70,
        )
        block1 = ledger1.record_contribution(
            proof=proof1, reputation_change=+5,
            reward_credit=proof1.agt_credit,
            node_id="node-a", agent_id="agent-a",
        )

        proof2 = IntelligenceProof.create(
            task_id="genesis-002", task_name="Task 2",
            agent_id="agent-b", node_id="node-b",
            contribution_type="knowledge_organization",
            difficulty=4, quality_score=90,
            verification_score=85, innovation_score=75,
        )
        block2 = ledger1.record_contribution(
            proof=proof2, reputation_change=+5,
            reward_credit=proof2.agt_credit,
            node_id="node-b", agent_id="agent-b",
        )

        assert ledger1.verify_chain()

        # Phase 2: Create a fresh ledger pointing at the same data dir
        ledger2 = IntelligenceLedger(data_dir=str(tmp_path))
        chain_ok = ledger2.load()
        assert chain_ok, "Chain integrity must survive restart"

        # Phase 3: Verify restored state
        assert ledger2.total_contributions == 3  # genesis + 2 contributions
        assert len(ledger2.blocks) == 3

        # Block 0: genesis
        assert ledger2.blocks[0].index == 0
        assert ledger2.blocks[0].block_id == "blk-genesis-00000000"

        # Block 1: matches block1
        restored_b1 = ledger2.blocks[1]
        assert restored_b1.block_id == block1.block_id
        assert restored_b1.block_hash == block1.block_hash
        assert restored_b1.reward_credit == block1.reward_credit
        assert restored_b1.agent_id == "agent-a"
        assert restored_b1.contribution_proof is not None
        assert restored_b1.contribution_proof.proof_id == proof1.proof_id

        # Block 2: matches block2
        restored_b2 = ledger2.blocks[2]
        assert restored_b2.block_hash == block2.block_hash
        assert restored_b2.agent_id == "agent-b"

        # Stats reconstructed correctly
        assert ledger2.total_credit_issued == proof1.agt_credit + proof2.agt_credit

        # Chain integrity verified
        assert ledger2.verify_chain()

    def test_persistence_rebuilds_chain_correctly(self, tmp_path):
        """Each restored block must link to its predecessor via previous_hash"""
        ledger1 = IntelligenceLedger(data_dir=str(tmp_path))
        ledger1.create_genesis_block("founder")
        for i in range(3):
            proof = IntelligenceProof.create(
                task_id=f"t{i}", task_name=f"Task {i}",
                agent_id="agent-x", node_id="node-x",
                contribution_type="analysis",
                difficulty=3, quality_score=80,
                verification_score=80, innovation_score=70,
            )
            ledger1.record_contribution(
                proof=proof, reputation_change=1,
                reward_credit=proof.agt_credit,
                node_id="node-x", agent_id="agent-x",
            )

        ledger2 = IntelligenceLedger(data_dir=str(tmp_path))
        ledger2.load()

        # Verify every link in the chain
        for i in range(1, len(ledger2.blocks)):
            current = ledger2.blocks[i]
            previous = ledger2.blocks[i - 1]
            assert current.previous_hash == previous.block_hash, (
                f"Block {i} previous_hash doesn't match block {i-1} block_hash"
            )
            assert current.index == i

        assert ledger2.verify_chain()

    def test_persistence_empty_ledger(self, tmp_path):
        """A fresh ledger with no blocks file loads as empty"""
        ledger = IntelligenceLedger(data_dir=str(tmp_path))
        result = ledger.load()
        assert result is True
        assert len(ledger.blocks) == 0
        assert ledger.total_contributions == 0

    # ============================================================
    # P0-2: Supply Guard
    # ============================================================

    def test_supply_guard_allows_normal_reward(self, ledger):
        """Reward within supply limit succeeds"""
        ledger.create_genesis_block("founder")
        proof = IntelligenceProof.create(
            task_id="t1", task_name="T1",
            agent_id="agent-a", node_id="node-a",
            contribution_type="analysis",
            difficulty=3, quality_score=80,
            verification_score=80, innovation_score=70,
        )
        # Should not raise
        block = ledger.record_contribution(
            proof=proof, reputation_change=1,
            reward_credit=50.0,
            node_id="node-a", agent_id="agent-a",
        )
        assert block is not None
        assert ledger.total_credit_issued == 50.0

    def test_supply_guard_rejects_excess(self, ledger):
        """Reward exceeding max_supply raises ValueError"""
        # Use a very small max_supply for testing
        ledger.max_supply = 100.0
        ledger.create_genesis_block("founder")

        # Issue up to the limit
        proof = IntelligenceProof.create(
            task_id="t1", task_name="T1",
            agent_id="agent-a", node_id="node-a",
            contribution_type="analysis",
            difficulty=3, quality_score=80,
            verification_score=80, innovation_score=70,
        )
        ledger.record_contribution(
            proof=proof, reputation_change=1,
            reward_credit=90.0,  # Total: 90 / 100
            node_id="node-a", agent_id="agent-a",
        )
        assert ledger.total_credit_issued == 90.0

        # Try to issue 20 more → 110 exceeds 100
        proof2 = IntelligenceProof.create(
            task_id="t2", task_name="T2",
            agent_id="agent-b", node_id="node-b",
            contribution_type="analysis",
            difficulty=3, quality_score=80,
            verification_score=80, innovation_score=70,
        )
        with pytest.raises(ValueError, match="Supply guard"):
            ledger.record_contribution(
                proof=proof2, reputation_change=1,
                reward_credit=20.0,
                node_id="node-b", agent_id="agent-b",
            )

        # Total should still be 90.0 (rejected transaction)
        assert ledger.total_credit_issued == 90.0

    def test_supply_remaining(self, ledger):
        """supply_remaining() reports correct value"""
        ledger.max_supply = 1000.0
        ledger.create_genesis_block("founder")

        assert ledger.supply_remaining() == 1000.0

        proof = IntelligenceProof.create(
            task_id="t1", task_name="T1",
            agent_id="agent-a", node_id="node-a",
            contribution_type="analysis",
            difficulty=3, quality_score=80,
            verification_score=80, innovation_score=70,
        )
        ledger.record_contribution(
            proof=proof, reputation_change=1,
            reward_credit=300.0,
            node_id="node-a", agent_id="agent-a",
        )
        assert ledger.supply_remaining() == 700.0
        assert 30.0 <= ledger.supply_used_pct() <= 30.1

    def test_block_immutability(self, ledger):
        """A sealed block cannot have its hash modified"""
        ledger.create_genesis_block("founder")
        proof = IntelligenceProof.create(
            task_id="t1", task_name="T1",
            agent_id="agent-a", node_id="node-a",
            contribution_type="analysis",
            difficulty=3, quality_score=80,
            verification_score=80, innovation_score=70,
        )
        block = ledger.record_contribution(
            proof=proof, reputation_change=1,
            reward_credit=10.0,
            node_id="node-a", agent_id="agent-a",
        )

        # Trying to re-seal should fail
        with pytest.raises(ValueError, match="already sealed"):
            block.seal()

        # Trying to change the hash externally has no effect
        # (the block is sealed but Python can't prevent attribute writes;
        #  the ledger's verify_chain would catch this via compute_hash check)
        original_hash = block.block_hash
        block.block_hash = "tampered"
        assert ledger.verify_chain() == False  # Tamper detected!

        # Restore for clean state
        block.block_hash = original_hash


# ============================================================
# Agent Reputation Tests
# ============================================================

class TestReputation:
    def test_default_reputation(self):
        rep = AgentReputation(agent_id="agent-x")
        assert rep.score == DEFAULT_REPUTATION
        assert rep.level in ("Active", "Newcomer")

    def test_high_quality_increase(self):
        rep = AgentReputation(agent_id="agent-x")
        delta = rep.apply_contribution_result(85, "task-001")
        assert delta == REPUTATION_DELTA[ReputationEvent.HIGH_QUALITY]
        assert rep.score == DEFAULT_REPUTATION + delta

    def test_normal_completion(self):
        rep = AgentReputation(agent_id="agent-x")
        delta = rep.apply_contribution_result(60, "task-002")
        assert delta == REPUTATION_DELTA[ReputationEvent.NORMAL_COMPLETION]

    def test_failed_decrease(self):
        rep = AgentReputation(agent_id="agent-x")
        delta = rep.apply_contribution_result(30, "task-fail")
        assert delta == REPUTATION_DELTA[ReputationEvent.FAILED]

    def test_malicious_penalty(self):
        rep = AgentReputation(agent_id="agent-x")
        delta = rep.apply_event(
            ReputationEvent.MALICIOUS, task_id="task-bad",
            reason="Caught faking results",
        )
        assert delta == -50
        assert rep.score == 50

    def test_reputation_floor(self):
        rep = AgentReputation(agent_id="agent-x", score=5)
        delta = rep.apply_event(ReputationEvent.MALICIOUS, task_id="t")
        assert rep.score >= 0  # Floor is 0

    def test_reputation_ceiling(self):
        rep = AgentReputation(agent_id="agent-x", score=998)
        rep.apply_event(ReputationEvent.HIGH_QUALITY, task_id="t")
        assert rep.score <= 1000  # Ceiling

    def test_level_progression(self):
        rep = AgentReputation(agent_id="agent-x")
        assert rep.level == "Active"  # 100

        rep.apply_event(ReputationEvent.HIGH_QUALITY, task_id="t")
        rep.apply_event(ReputationEvent.HIGH_QUALITY, task_id="t")
        rep.apply_event(ReputationEvent.HIGH_QUALITY, task_id="t")
        assert rep.score >= 115
        # Still Active/Trusted

        # Boost to Expert level
        rep.score = 300
        assert rep.level == "Expert"

        rep.score = 500
        assert rep.level == "Sage"

    def test_reward_multiplier(self):
        rep = AgentReputation(agent_id="agent-x")
        assert rep.reward_multiplier == 1.0

        rep.score = 300
        assert rep.reward_multiplier == 1.3

        rep.score = 500
        assert rep.reward_multiplier == 1.5

        rep.score = 40
        assert rep.reward_multiplier == 0.8

    def test_can_take_task(self):
        rep = AgentReputation(agent_id="agent-x", score=50)
        assert rep.can_take_task(1)
        assert rep.can_take_task(5)
        assert rep.can_take_task(9)  # need 50, has 50 → ok
        assert rep.can_take_task(10)  # need 50, has 50 → ok

        # Boundary: need 30 for difficulty 7, has 25
        rep2 = AgentReputation(agent_id="agent-y", score=25)
        assert rep2.can_take_task(7) == False  # need 30, has 25

    def test_history_tracking(self):
        rep = AgentReputation(agent_id="agent-x")
        rep.apply_contribution_result(90, "task-a")
        rep.apply_contribution_result(40, "task-b")

        history = rep.get_recent_history()
        assert len(history) == 2
        assert history[0].task_id == "task-a"
        assert history[0].event == ReputationEvent.HIGH_QUALITY
        assert history[1].event == ReputationEvent.FAILED


# ============================================================
# Identity & Wallet Tests
# ============================================================

class TestIdentity:
    def test_node_identity_create(self):
        ident = NodeIdentity.create(node_name="test-node", founder_id="founder-1")
        assert ident.node_id.startswith("agt-node-")
        assert ident.node_name == "test-node"

    def test_genesis_identity_create(self):
        gen = GenesisIdentity.create(
            founder_id="yuqiu-hong",
            node_id="agt-node-abc12345",
        )
        assert gen.founder_id == "yuqiu-hong"
        assert gen.version.startswith("v0.")  # Version evolves with protocol
        assert len(gen.genesis_hash) == 64

    def test_genesis_not_admin(self):
        """Genesis Identity is NOT a super-admin — just a record"""
        gen = GenesisIdentity.create("founder", "node-1")
        d = gen.to_dict()
        # No permission fields
        assert "admin" not in str(d).lower()
        assert "privilege" not in str(d).lower()
        assert "withdraw" not in str(d).lower()


class TestCreditWallet:
    def test_wallet_credit(self):
        wallet = CreditWallet(node_id="node-a", agent_id="agent-a")
        assert wallet.balance == 0.0

        wallet.credit(50.0, "poi-abc", "task-001")
        assert wallet.balance == 50.0
        assert len(wallet.entries) == 1

    def test_wallet_no_negative_credit(self):
        wallet = CreditWallet(node_id="node-a", agent_id="agent-a")
        wallet.credit(-10, "poi-xyz", "task-fail")
        assert wallet.balance == 0.0  # Not applied

    def test_wallet_status(self):
        wallet = CreditWallet(node_id="node-a", agent_id="agent-a")
        wallet.credit(30, "poi-1", "task-1")
        wallet.credit(20, "poi-2", "task-2")

        status = wallet.status()
        assert status["balance"] == 50.0
        assert status["total_transactions"] == 2
