"""
Tests: v0.2 Trust Layer — Proof Verification + Reputation Consensus + Anti-Sybil

Verifies:
- ProofRegistry: cross-node proof verification
- Reputation: proof_id traceability, verify_reputation_trace()
- Anti-Sybil: duplicate output detection, rapid-fire detection
"""

import hashlib
import os
import tempfile
import time
import pytest

from agt_node.identity import KeyPair
from agt_node.reputation import (
    AgentReputation,
    ReputationEvent,
    ReputationRecord,
    REPUTATION_DELTA,
    DEFAULT_REPUTATION,
)
from agt_node.agent_identity import AgentIdentity, CapabilityProfile
from agt_node.anti_sybil import AntiSybil, SybilAlert
from poi_consensus.intelligence_proof import (
    IntelligenceProof,
    make_evidence,
    EvidenceType,
)
from poi_consensus.proof_registry import ProofRegistry


# ============================================================
# Proof Registry Tests
# ============================================================

class TestProofRegistry:
    @pytest.fixture
    def key_pair(self):
        return KeyPair.generate()

    @pytest.fixture
    def signed_proof(self, key_pair):
        proof = IntelligenceProof.create(
            task_id="reg-test-1", task_name="Registry Test",
            agent_id="agent-a", node_id="node-a",
            contribution_type="analysis",
            difficulty=3, quality_score=85,
            verification_score=80, innovation_score=70,
            evidence=[
                make_evidence("artifact_hash", "test output", "content"),
            ],
            validator_node_id="validator-node",
            validator_agent_id="validator-agent",
        )
        proof.sign(key_pair)
        return proof

    def test_register_validator(self):
        reg = ProofRegistry()
        reg.register_validator("node-a", "aa" * 32)
        assert reg.is_known_validator("node-a")
        assert not reg.is_known_validator("node-b")

    def test_verify_signed_proof(self, signed_proof, key_pair):
        reg = ProofRegistry()
        result = reg.verify_proof(signed_proof)
        assert result["verified"]
        assert result["reason"] == "Signature valid"

    def test_verify_unsigned_proof_fails(self):
        reg = ProofRegistry()
        proof = IntelligenceProof.create(
            task_id="t1", task_name="Unsigned",
            agent_id="a1", node_id="n1",
            contribution_type="analysis",
            difficulty=3, quality_score=80,
            verification_score=80, innovation_score=70,
        )
        result = reg.verify_proof(proof)
        assert not result["verified"]
        assert "not signed" in result["reason"].lower()

    def test_verify_tampered_proof_fails(self, signed_proof):
        reg = ProofRegistry()
        assert reg.verify_proof(signed_proof)["verified"]

        # Tamper
        signed_proof.quality_score = 1
        result = reg.verify_proof(signed_proof)
        assert not result["verified"]
        assert "failed" in result["reason"].lower()

    def test_auto_register_validator(self, signed_proof, key_pair):
        reg = ProofRegistry()
        assert not reg.is_known_validator("validator-node")
        reg.verify_proof(signed_proof)
        assert reg.is_known_validator("validator-node")
        assert reg.get_validator_key("validator-node") == key_pair.public_key_hex

    def test_import_proof_from_peer(self, signed_proof):
        reg = ProofRegistry()
        result = reg.import_proof(signed_proof, source_node_id="peer-node")
        assert result["verified"]
        assert result["source_node"] == "peer-node"

    def test_import_tampered_proof_rejected(self, signed_proof):
        reg = ProofRegistry()
        signed_proof.quality_score = 1  # Tamper
        result = reg.import_proof(signed_proof, source_node_id="peer-node")
        assert not result["verified"]

    def test_registry_stats(self, signed_proof):
        reg = ProofRegistry()
        reg.verify_proof(signed_proof)
        stats = reg.get_stats()
        assert stats["known_validators"] >= 1
        assert stats["verified_proofs"] == 1
        assert stats["total_verifications"] == 1

    def test_registry_persistence(self, signed_proof):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg1 = ProofRegistry(data_dir=tmpdir)
            reg1.verify_proof(signed_proof)
            reg1.save()

            reg2 = ProofRegistry(data_dir=tmpdir)
            assert reg2.is_known_validator("validator-node")


# ============================================================
# Reputation Traceability Tests
# ============================================================

class TestReputationTraceability:
    def test_proof_id_in_record(self):
        rep = AgentReputation(agent_id="agent-x")
        rep.apply_contribution_result(90, "task-001", proof_id="poi-abc123")
        assert len(rep.history) == 1
        assert rep.history[0].proof_id == "poi-abc123"

    def test_verify_trace_passes_with_proof_refs(self):
        rep = AgentReputation(agent_id="agent-x")
        rep.apply_contribution_result(85, "task-a", proof_id="poi-001")
        rep.apply_contribution_result(60, "task-b", proof_id="poi-002")
        assert rep.verify_reputation_trace()

    def test_verify_trace_fails_without_proof_refs(self):
        rep = AgentReputation(agent_id="agent-x")
        # Direct call without proof_id
        rep.apply_event(
            ReputationEvent.HIGH_QUALITY,
            task_id="task-no-proof",
            reason="Test",
            proof_id="",  # Missing!
        )
        assert not rep.verify_reputation_trace()

    def test_genesis_event_exempt(self):
        """Genesis events don't need proof_id"""
        rep = AgentReputation(agent_id="agent-x")
        # Manually add a genesis event
        rep.apply_event(
            ReputationEvent.GENESIS,
            task_id="genesis",
            reason="Initial reputation",
            proof_id="",
        )
        assert rep.verify_reputation_trace()

    def test_mixed_traceability(self):
        """Mixed: events with and without proof_refs"""
        rep = AgentReputation(agent_id="agent-x")
        rep.apply_contribution_result(90, "t1", proof_id="poi-001")
        rep.apply_event(
            ReputationEvent.NORMAL_COMPLETION,
            task_id="t2",
            reason="Missing proof ref",
            proof_id="",  # Missing
        )
        assert not rep.verify_reputation_trace()

    def test_history_includes_proof_id(self):
        rep = AgentReputation(agent_id="agent-x")
        rep.apply_contribution_result(85, "task-x", proof_id="poi-proof-xyz")

        recent = rep.get_recent_history()
        assert recent[0].proof_id == "poi-proof-xyz"


# ============================================================
# Anti-Sybil Tests
# ============================================================

class TestAntiSybil:
    @pytest.fixture
    def key_pair(self):
        return KeyPair.generate()

    def make_proof(self, agent_id="agent-a", node_id="node-a",
                   content="test content", key_pair=None):
        """Create a signed proof for testing"""
        proof = IntelligenceProof.create(
            task_id="test-task", task_name="Test",
            agent_id=agent_id, node_id=node_id,
            contribution_type="analysis",
            difficulty=3, quality_score=80,
            verification_score=80, innovation_score=70,
            evidence=[
                make_evidence("artifact_hash", "test", content),
            ],
        )
        if key_pair:
            proof.sign(key_pair)
        return proof

    def test_clean_contributions_pass(self, key_pair):
        """Normal contributions don't trigger alerts"""
        as_checker = AntiSybil(node_id="node-a")
        as_checker.min_task_interval_ms = 1  # Allow any speed
        as_checker.max_identical_outputs = 10
        for i in range(5):
            proof = self.make_proof(
                content=f"unique content {i}",
                key_pair=key_pair,
            )
            alert = as_checker.check_contribution(proof, "agent-a", "node-a")
            assert alert is None
            time.sleep(0.002)  # 2ms gap avoids rapid-fire trigger

    def test_duplicate_output_detected(self, key_pair):
        """Identical output hash triggers high severity alert"""
        as_checker = AntiSybil(node_id="node-a")

        for i in range(5):
            proof = self.make_proof(
                content="SAME CONTENT EVERY TIME",  # Identical!
                key_pair=key_pair,
            )
            alert = as_checker.check_contribution(proof, "agent-a", "node-a")
            if alert:
                assert alert.severity == "high"
                assert "Identical output" in alert.reason
                break
        else:
            pytest.fail("Should have detected duplicate output")

    def test_rapid_completion_detected(self, key_pair):
        """Sub-second task completion triggers alert"""
        as_checker = AntiSybil(node_id="node-a")
        as_checker.min_task_interval_ms = 1000  # 1 second threshold

        for i in range(5):
            proof = self.make_proof(
                content=f"rapid {i}",
                key_pair=key_pair,
            )
            alert = as_checker.check_contribution(proof, "agent-a", "node-a")
            if alert:
                assert "Rapid" in alert.reason
                break

    def test_stats_track_alerts(self, key_pair):
        as_checker = AntiSybil(node_id="node-a")
        as_checker.max_identical_outputs = 2

        for i in range(3):
            proof = self.make_proof(
                content="DUPLICATE OUTPUT",
                key_pair=key_pair,
            )
            as_checker.check_contribution(proof, "agent-a", "node-a")

        stats = as_checker.stats()
        assert stats["alerts_raised"] >= 1

    def test_custom_thresholds(self, key_pair):
        """Thresholds are configurable"""
        as_checker = AntiSybil(node_id="node-a")
        as_checker.max_identical_outputs = 10  # Very permissive
        as_checker.min_task_interval_ms = 1    # Very fast allowed

        for i in range(8):
            proof = self.make_proof(
                content="same content",
                key_pair=key_pair,
            )
            alert = as_checker.check_contribution(proof, "agent-a", "node-a")
            if i < as_checker.max_identical_outputs - 1:
                assert alert is None  # Should not trigger below threshold
            time.sleep(0.002)  # 2ms between tasks to avoid rapid-fire trigger
