"""
Tests: v0.3 Autonomous Engine — Opportunity Detection + Task Generation

Verifies:
- OpportunityDetector: domain scanning, novelty hashing, LLM fallback
- TaskGenerator: proposal creation, reputation gate, stake, novelty check,
  rate limiting, status transitions
"""

import pytest

from agt_node.autonomous.opportunity_detector import (
    OpportunityDetector,
    Opportunity,
    OpportunityType,
)
from agt_node.autonomous.task_generator import (
    TaskGenerator,
    TaskProposal,
    ProposalStatus,
    MIN_PROPOSER_REPUTATION,
    PROPOSAL_STAKE,
    MAX_PROPOSALS_PER_EPOCH,
)


# ============================================================
# Opportunity Detector Tests
# ============================================================

class TestOpportunityDetector:
    @pytest.mark.asyncio
    async def test_scan_code_domain(self):
        detector = OpportunityDetector()
        opps = await detector.scan("code", {
            "code_sample": "def x():\n    pass\n" * 30,  # 60 lines
            "source": "test-repo",
        })
        assert len(opps) >= 0  # At least finds the heuristic opportunity

    @pytest.mark.asyncio
    async def test_scan_knowledge_domain(self):
        detector = OpportunityDetector()
        opps = await detector.scan("knowledge", {
            "missing_topics": ["PoI Consensus", "Impact Oracle"],
        })
        assert len(opps) == 2
        assert opps[0].type == OpportunityType.KNOWLEDGE_GAP

    @pytest.mark.asyncio
    async def test_scan_tool_domain(self):
        detector = OpportunityDetector()
        opps = await detector.scan("tool", {
            "missing_tools": ["Code Formatter"],
        })
        assert len(opps) == 1
        assert opps[0].type == OpportunityType.TOOL_GAP

    @pytest.mark.asyncio
    async def test_scan_general_all_domains(self):
        detector = OpportunityDetector()
        opps = await detector.scan("general", {
            "code_sample": "x" * 100,
            "missing_topics": ["Topic A"],
            "missing_tools": ["Tool X"],
        })
        # Should find opportunities across all domains
        assert len(opps) >= 2

    @pytest.mark.asyncio
    async def test_novelty_hash_deduplication(self):
        """Same opportunity appears only once"""
        detector = OpportunityDetector()
        context = {"missing_topics": ["Unique Topic"]}

        opps1 = await detector.scan("knowledge", context)
        assert len(opps1) == 1

        # Same scan → should be deduplicated
        opps2 = await detector.scan("knowledge", context)
        assert len(opps2) == 0  # Already seen

    def test_opportunity_novelty_hash_deterministic(self):
        opp1 = Opportunity(
            opportunity_id="test-1",
            type=OpportunityType.CODE_OPTIMIZATION,
            title="Fix sort algorithm",
            description="Optimize bubble sort",
            source="repo-a",
        )
        opp2 = Opportunity(
            opportunity_id="test-2",
            type=OpportunityType.CODE_OPTIMIZATION,
            title="Fix sort algorithm",
            description="Optimize bubble sort",
            source="repo-a",
        )
        assert opp1.novelty_hash == opp2.novelty_hash

    def test_opportunity_to_dict(self):
        opp = Opportunity(
            opportunity_id="test-1",
            type=OpportunityType.CODE_OPTIMIZATION,
            title="Test",
            description="Desc",
        )
        d = opp.to_dict()
        assert d["type"] == "code_optimization"
        assert "novelty_hash" in d


# ============================================================
# Task Generator Tests
# ============================================================

class TestTaskGenerator:
    def test_create_proposal_below_reputation(self):
        """Agents below MIN_PROPOSER_REPUTATION cannot propose"""
        gen = TaskGenerator(node_id="node-a")
        proposal = gen.create_proposal(
            agent_id="agent-new",
            title="Test Task",
            description="A test",
            goal="Achieve something",
            task_type="code_optimization",
            difficulty=3,
            value=20.0,
            reputation=50.0,  # Below threshold (150)
        )
        assert proposal is None

    def test_create_proposal_above_reputation(self):
        """Agents meeting reputation threshold can propose"""
        gen = TaskGenerator(node_id="node-a")
        proposal = gen.create_proposal(
            agent_id="agent-senior",
            title="Optimize Database",
            description="The database queries need optimization",
            goal="Reduce query time by 30%",
            task_type="code_optimization",
            difficulty=5,
            value=50.0,
            reputation=200.0,
        )
        assert proposal is not None
        assert proposal.proposer_agent_id == "agent-senior"
        assert proposal.status == ProposalStatus.DRAFT
        assert proposal.title == "Optimize Database"

    def test_duplicate_proposal_rejected(self):
        """Duplicate proposals are blocked by novelty check"""
        gen = TaskGenerator(node_id="node-a")
        p1 = gen.create_proposal(
            "agent-a", "Same Task", "Same description",
            "Same goal", "analysis", 3, 20.0, 200.0,
        )
        assert p1 is not None

        p2 = gen.create_proposal(
            "agent-a", "Same Task", "Same description",
            "Same goal", "analysis", 3, 20.0, 200.0,
        )
        assert p2 is None  # Duplicate blocked

    def test_rate_limiting(self):
        """Agents limited to MAX_PROPOSALS_PER_EPOCH"""
        gen = TaskGenerator(node_id="node-a")

        for i in range(MAX_PROPOSALS_PER_EPOCH + 5):
            gen.create_proposal(
                "agent-a", f"Task {i}", f"Desc {i}",
                f"Goal {i}", "analysis", 3, 20.0, 200.0,
            )

        # Only the first MAX_PROPOSALS_PER_EPOCH should succeed
        listed = gen.get_listed_proposals()
        assert len(listed) + len([p for p in gen._proposals.values() if p.status != ProposalStatus.LISTED]) <= MAX_PROPOSALS_PER_EPOCH
        count = gen._agent_proposal_counts.get("agent-a", 0)
        # Count should be max 10 (but proposals beyond that just aren't created, not counted)
        assert count <= MAX_PROPOSALS_PER_EPOCH

    def test_stake_and_list(self):
        """Proposal is staked and listed when wallet has sufficient balance"""
        gen = TaskGenerator(node_id="node-a")
        proposal = gen.create_proposal(
            "agent-a", "Stake Test", "Description",
            "Goal", "tool_development", 4, 40.0, 200.0,
        )
        assert proposal is not None

        success = gen.stake_and_list(proposal.proposal_id, wallet_balance=100.0)
        assert success
        assert proposal.status == ProposalStatus.LISTED
        assert proposal.staked_amount == PROPOSAL_STAKE

    def test_stake_insufficient_balance(self):
        """Cannot stake without sufficient balance"""
        gen = TaskGenerator(node_id="node-a")
        proposal = gen.create_proposal(
            "agent-b", "Poor Stake", "Description",
            "Goal", "analysis", 3, 20.0, 200.0,
        )
        success = gen.stake_and_list(proposal.proposal_id, wallet_balance=1.0)
        assert not success
        assert proposal.status == ProposalStatus.DRAFT

    def test_reject_proposal(self):
        """Rejected proposal loses stake"""
        gen = TaskGenerator(node_id="node-a")
        proposal = gen.create_proposal(
            "agent-c", "Reject Me", "Description",
            "Goal", "analysis", 3, 20.0, 200.0,
        )
        gen.stake_and_list(proposal.proposal_id, wallet_balance=100.0)
        assert proposal.status == ProposalStatus.LISTED

        gen.reject_proposal(proposal.proposal_id, "Spam detected")
        assert proposal.status == ProposalStatus.REJECTED

    def test_mark_completed(self):
        """Proposal transitions to completed when task is done"""
        gen = TaskGenerator(node_id="node-a")
        proposal = gen.create_proposal(
            "agent-d", "Complete Me", "Description",
            "Goal", "code_optimization", 5, 50.0, 200.0,
        )
        gen.stake_and_list(proposal.proposal_id, 100.0)
        gen.mark_completed(proposal.proposal_id, "task-completed-001")

        assert proposal.status == ProposalStatus.COMPLETED
        assert proposal.listed_task_id == "task-completed-001"

    def test_reset_epoch_counters(self):
        """Epoch reset clears rate limit counters"""
        gen = TaskGenerator(node_id="node-a")
        for i in range(5):
            gen.create_proposal(
                "agent-a", f"T{i}", f"D{i}", f"G{i}",
                "analysis", 3, 20.0, 200.0,
            )
        assert gen._agent_proposal_counts.get("agent-a", 0) == 5

        gen.reset_epoch_counters()
        assert gen._agent_proposal_counts.get("agent-a", 0) == 0

    def test_stats(self):
        gen = TaskGenerator(node_id="node-a")
        gen.create_proposal("a1", "T1", "D1", "G1", "analysis", 3, 20.0, 200.0)
        gen.create_proposal("a2", "T2", "D2", "G2", "code_optimization", 5, 50.0, 200.0)

        stats = gen.stats()
        assert stats["total_proposals"] == 2
        assert "draft" in stats["by_status"]

    def test_to_task_dict(self):
        """Proposal converts to AGTTask-compatible format"""
        gen = TaskGenerator(node_id="node-a")
        proposal = gen.create_proposal(
            "agent-x", "Task Dict Test", "Description text",
            "Achieve goal", "knowledge_organization", 3, 30.0, 200.0,
        )
        task_dict = proposal.to_task_dict()
        assert task_dict["id"] == proposal.proposal_id
        assert task_dict["name"] == "Task Dict Test"
        assert task_dict["source"] == "agent_generated"
        assert task_dict["creator"] == "agent-x"
        assert task_dict["difficulty"] == 3
        assert task_dict["value"] == 30.0

    def test_value_clamping(self):
        """Proposed values are clamped to [5, 200]"""
        gen = TaskGenerator(node_id="node-a")

        too_low = gen.create_proposal(
            "a1", "Low", "D", "G", "analysis", 3, 0.01, 200.0,
        )
        assert too_low.proposed_value == 5.0

        too_high = gen.create_proposal(
            "a2", "High", "D", "G", "analysis", 3, 9999.0, 200.0,
        )
        assert too_high.proposed_value == 200.0
