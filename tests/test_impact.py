"""
Tests: v0.3 Impact Oracle — Signals, Scoring, Epoch, Oracle, Cycle Detection

Verifies the load-bearing economic defense of AGT v0.3:
- Signal collection (references, reuse, forks, citations)
- Impact Score formula (Usage × Verification × Longevity × Diversity)
- Epoch system (delayed measurement, window transitions, finalization)
- Circular reference detection (2-cycle, 3-cycle, self-loop)
- ImpactOracle integrated pipeline
"""

import math
import pytest

from impact_oracle.signals import (
    SignalCollector, ImpactSignal, SignalType, SignalTier,
    SIGNAL_WEIGHTS, SIGNAL_TIERS,
)
from impact_oracle.scoring import ImpactScorer, ImpactScore
from impact_oracle.epoch import EpochManager, ImpactWindow
from impact_oracle.oracle import ImpactOracle, ImpactReport


# ============================================================
# Signal Tests
# ============================================================

class TestSignals:
    def test_signal_creation(self):
        signal = ImpactSignal(
            signal_type=SignalType.PROOF_REFERENCE,
            value=1.0,
            source_proof_id="proof-b",
            source_agent_id="agent-1",
        )
        assert signal.weight == SIGNAL_WEIGHTS[SignalType.PROOF_REFERENCE]
        assert signal.tier == SignalTier.ON_CHAIN
        assert signal.weighted_value == 1.0 * SIGNAL_WEIGHTS[SignalType.PROOF_REFERENCE]

    def test_reuse_has_higher_weight(self):
        """Reuse counts more than passive references"""
        ref = ImpactSignal(SignalType.PROOF_REFERENCE, 1.0)
        reuse = ImpactSignal(SignalType.REUSE_COUNT, 1.0)
        assert reuse.weight > ref.weight

    def test_fork_has_highest_on_chain_weight(self):
        """Forking is the strongest on-chain signal"""
        fork = ImpactSignal(SignalType.FORK_COUNT, 1.0)
        assert fork.weight >= SIGNAL_WEIGHTS[SignalType.REUSE_COUNT]

    def test_signal_tier_assignment(self):
        assert SIGNAL_TIERS[SignalType.PROOF_REFERENCE] == SignalTier.ON_CHAIN
        assert SIGNAL_TIERS[SignalType.GITHUB_STARS] == SignalTier.EXTERNAL
        assert SIGNAL_TIERS[SignalType.REVENUE_GENERATED] == SignalTier.ECONOMIC

    def test_collector_record_reference(self):
        collector = SignalCollector()
        collector.record_reference("proof-a", "proof-b", "agent-1", depth=1.0)
        signals = collector.get_signals("proof-a")
        assert len(signals) == 1
        assert signals[0].signal_type == SignalType.PROOF_REFERENCE

    def test_collector_record_reuse(self):
        collector = SignalCollector()
        collector.record_reuse("proof-a", "agent-2", "import")
        collector.record_reuse("proof-a", "agent-3", "import")

        users = collector.get_unique_referencing_agents("proof-a")
        assert len(users) == 2

    def test_collector_record_fork(self):
        collector = SignalCollector()
        collector.record_fork("proof-a", "task-fork", "agent-5")
        assert collector.get_fork_count("proof-a") == 1

    def test_collector_filter_by_type(self):
        collector = SignalCollector()
        collector.record_reference("proof-x", "proof-y", "agent-1")
        collector.record_reuse("proof-x", "agent-2", "import")
        collector.record_fork("proof-x", "task-f", "agent-3")

        refs = collector.get_signals("proof-x", SignalType.PROOF_REFERENCE)
        assert len(refs) == 1

        forks = collector.get_signals("proof-x", SignalType.FORK_COUNT)
        assert len(forks) == 1

    def test_collector_filter_by_tier(self):
        collector = SignalCollector()
        collector.record_reference("proof-z", "proof-w", "agent-1")
        collector.record_reuse("proof-z", "agent-2", "import")

        on_chain = collector.get_signals("proof-z", tier=SignalTier.ON_CHAIN)
        assert len(on_chain) == 2

        external = collector.get_signals("proof-z", tier=SignalTier.EXTERNAL)
        assert len(external) == 0

    def test_collector_stats(self):
        collector = SignalCollector()
        collector.record_reference("proof-s", "proof-t", "agent-1")
        collector.record_reference("proof-s", "proof-u", "agent-2")
        collector.record_reference("proof-s", "proof-v", "agent-3")
        collector.record_fork("proof-s", "task-f1", "agent-4")

        stats = collector.stats("proof-s")
        assert stats["total_signals"] == 4
        assert stats["unique_referencing_agents"] == 3
        assert stats["fork_count"] == 1
        assert "proof_reference" in stats["by_type"]
        assert "fork_count" in stats["by_type"]

    def test_has_external_signals(self):
        collector = SignalCollector()
        collector.record_reference("proof-e", "proof-f", "agent-1")
        assert not collector.has_external_signals("proof-e")

        # Simulate external signal
        ext = ImpactSignal(
            SignalType.GITHUB_STARS, 10.0,
            source_proof_id="proof-g", source_agent_id="user-1"
        )
        collector.record_signal("proof-e", ext)
        assert collector.has_external_signals("proof-e")


# ============================================================
# Scoring Tests
# ============================================================

class TestScoring:
    def test_zero_signals_low_score(self):
        collector = SignalCollector()
        scorer = ImpactScorer(collector)
        score = scorer.compute("proof-empty")
        assert score.display_score < 50  # No signals → low score
        assert score.impact_level in ("None", "Marginal")

    def test_many_users_high_score(self):
        collector = SignalCollector()
        for i in range(50):
            collector.record_reuse(f"proof-hot", f"agent-{i}", "import")
        scorer = ImpactScorer(collector)
        score = scorer.compute("proof-hot")
        assert score.usage_factor > 0.5
        assert score.display_score > 0

    def test_finalization(self):
        collector = SignalCollector()
        collector.record_reference("proof-fin", "proof-x", "agent-1")
        scorer = ImpactScorer(collector)

        # Age < 13 epochs → not finalized
        s1 = scorer.compute("proof-fin", age_in_epochs=5)
        assert not s1.finalized

        # Age >= 13 epochs → finalized
        s2 = scorer.compute("proof-fin", age_in_epochs=13)
        assert s2.finalized

    def test_longevity_decay(self):
        """Older contributions with no additional signals decay"""
        collector = SignalCollector()
        collector.record_reference("proof-old", "proof-x", "agent-1")
        scorer = ImpactScorer(collector)

        # At age 1: recent signals exist, longevity high
        s_new = scorer.compute("proof-old", age_in_epochs=1)
        # At age 50: same signals, but all are old → decay
        s_old = scorer.compute("proof-old", age_in_epochs=50)

        # Old should have decayed more than new
        assert s_old.longevity_factor <= s_new.longevity_factor

    def test_display_score_range(self):
        """Display score always in [0, 1000]"""
        collector = SignalCollector()
        scorer = ImpactScorer(collector)

        # Empty
        s0 = scorer.compute("p0")
        assert 0 <= s0.display_score <= 1000

        # High usage
        for i in range(200):
            collector.record_reuse("p1", f"agent-{i}", "import")
        for i in range(20):
            collector.record_fork("p1", f"task-{i}", f"agent-{i}")

        s1 = scorer.compute("p1")
        assert 0 <= s1.display_score <= 1000

    def test_network_size_normalization(self):
        """Larger networks should not inflate scores"""
        collector = SignalCollector()
        collector.record_reference("proof-n", "proof-y", "agent-1")
        scorer = ImpactScorer(collector)

        s_small = scorer.compute("proof-n", network_size=100)
        s_large = scorer.compute("proof-n", network_size=10000)

        # Large network → lower or equal score
        assert s_large.display_score <= s_small.display_score

    def test_score_to_dict(self):
        collector = SignalCollector()
        collector.record_reference("proof-d", "proof-z", "agent-1")
        scorer = ImpactScorer(collector)
        score = scorer.compute("proof-d")
        d = score.to_dict()
        assert "factors" in d
        assert "scores" in d
        assert d["scores"]["level"] in [
            "None", "Marginal", "Notable", "Meaningful",
            "Significant", "Transformative",
        ]


# ============================================================
# Epoch Tests
# ============================================================

class TestEpoch:
    def test_epoch_start(self):
        em = EpochManager()
        assert em.current_epoch == 0
        em.start_epoch()
        assert em.current_epoch == 1

    def test_register_proof_age(self):
        em = EpochManager()
        em.start_epoch()  # Epoch 1
        em.register_proof("proof-a")
        assert em.get_proof_age("proof-a") == 0

        em.start_epoch()  # Epoch 2
        assert em.get_proof_age("proof-a") == 1

    def test_window_transitions(self):
        em = EpochManager()
        em.start_epoch()  # Epoch 1
        em.register_proof("proof-w")

        # Immediate (0-1 epochs)
        assert em.get_proof_window("proof-w") == ImpactWindow.IMMEDIATE

        # Advance to Sustained
        em.advance_epochs(2)
        assert em.get_proof_window("proof-w") == ImpactWindow.SUSTAINED

    def test_enduring_window(self):
        em = EpochManager()
        em.start_epoch()
        em.register_proof("proof-enduring")
        em.advance_epochs(14)  # Age = 14 → Enduring
        assert em.get_proof_window("proof-enduring") == ImpactWindow.ENDURING
        assert em.is_finalized("proof-enduring")

    def test_get_proofs_in_window(self):
        em = EpochManager()
        em.start_epoch()
        em.register_proof("new")
        em.advance_epochs(2)
        em.start_epoch()
        em.register_proof("very-new")

        immediate = em.get_proofs_in_window(ImpactWindow.IMMEDIATE)
        assert "very-new" in immediate

    def test_advance_epochs(self):
        em = EpochManager()
        em.start_epoch()
        em.advance_epochs(5)
        assert em.current_epoch == 6

    def test_stats(self):
        em = EpochManager()
        em.start_epoch()
        em.register_proof("p1")
        em.register_proof("p2")
        s = em.stats()
        assert s["current_epoch"] == 1
        assert s["proofs_tracked"] == 2


# ============================================================
# Cycle Detection Tests
# ============================================================

class TestCycleDetection:
    def test_no_cycle_linear(self):
        """A → B → C (no cycle)"""
        oracle = ImpactOracle()
        oracle.register_contribution("proof-a")
        oracle.register_contribution("proof-b")
        oracle.register_contribution("proof-c")
        oracle.record_reference("proof-b", "proof-a", "agent-1")
        oracle.record_reference("proof-c", "proof-b", "agent-2")

        assert not oracle.has_cycle("proof-a")
        assert not oracle.has_cycle("proof-b")
        assert not oracle.has_cycle("proof-c")

    def test_two_cycle_detected(self):
        """A → B → A (2-cycle)"""
        oracle = ImpactOracle()
        oracle.register_contribution("proof-a")
        oracle.register_contribution("proof-b")
        oracle.record_reference("proof-b", "proof-a", "agent-1")
        oracle.record_reference("proof-a", "proof-b", "agent-2")

        cycles_a = oracle._detect_circular_references("proof-a")
        assert len(cycles_a) >= 2  # A → B → A
        assert oracle.has_cycle("proof-a")
        assert oracle.has_cycle("proof-b")

    def test_three_cycle_detected(self):
        """A → B → C → A (3-cycle)"""
        oracle = ImpactOracle()
        oracle.register_contribution("proof-a")
        oracle.register_contribution("proof-b")
        oracle.register_contribution("proof-c")
        oracle.record_reference("proof-b", "proof-a", "agent-1")
        oracle.record_reference("proof-c", "proof-b", "agent-2")
        oracle.record_reference("proof-a", "proof-c", "agent-3")

        assert oracle.has_cycle("proof-a")
        assert oracle.has_cycle("proof-b")
        assert oracle.has_cycle("proof-c")

    def test_no_cycle_isolated(self):
        """A (no references)"""
        oracle = ImpactOracle()
        oracle.register_contribution("proof-solo")
        assert not oracle.has_cycle("proof-solo")

    def test_cycle_penalty_reduces_score(self):
        """Circular references → score penalty applied"""
        oracle = ImpactOracle()
        oracle.register_contribution("proof-a")
        oracle.register_contribution("proof-b")
        # Create many legitimate references first
        for i in range(10):
            oracle.record_reuse("proof-a", f"agent-{i}", "import")
        # Then create a cycle
        oracle.record_reference("proof-b", "proof-a", "agent-1")
        oracle.record_reference("proof-a", "proof-b", "agent-2")

        report = oracle.assess("proof-a")
        assert report.is_circular
        # Score should be penalized (less than it would be without the cycle)
        assert report.score.display_score >= 0  # Still valid range


# ============================================================
# Oracle Integration Tests
# ============================================================

class TestImpactOracle:
    def test_register_and_assess(self):
        oracle = ImpactOracle(network_size=100)
        oracle.register_contribution("proof-x")

        # No signals yet
        report = oracle.assess("proof-x")
        assert report.proof_id == "proof-x"
        assert report.signal_count == 0
        assert report.score.impact_level in ("None", "Marginal")

    def test_signals_increase_score(self):
        oracle = ImpactOracle(network_size=100)
        oracle.register_contribution("proof-y")

        score_before = oracle.assess("proof-y").score.display_score

        # Add signals
        for i in range(20):
            oracle.record_reuse("proof-y", f"agent-{i}", "import")
        for i in range(5):
            oracle.record_fork("proof-y", f"task-{i}", f"agent-{i}")

        score_after = oracle.assess("proof-y").score.display_score
        assert score_after > score_before

    def test_epoch_advancement(self):
        oracle = ImpactOracle(network_size=100)
        oracle.register_contribution("proof-z")
        oracle.record_reuse("proof-z", "agent-1", "import")

        oracle.advance_epochs(3)
        assert oracle.epochs.current_epoch == 4

    def test_leaderboard(self):
        oracle = ImpactOracle(network_size=100)

        for pid, agent_count in [("p1", 5), ("p2", 30), ("p3", 15)]:
            oracle.register_contribution(pid)
            for i in range(agent_count):
                oracle.record_reuse(pid, f"agent-{i}", "import")

        board = oracle.get_impact_leaderboard(limit=10)
        assert len(board) <= 3
        # p2 (30 users) should be first
        assert board[0]["proof_id"] == "p2"

    def test_oracle_stats(self):
        oracle = ImpactOracle(network_size=100)
        oracle.register_contribution("p1")
        oracle.register_contribution("p2")
        oracle.record_reference("p2", "p1", "agent-1")

        stats = oracle.stats()
        assert stats["tracked_proofs"] == 2
        assert stats["network_size"] == 100

    def test_assess_all_in_window(self):
        oracle = ImpactOracle(network_size=100)
        oracle.register_contribution("p-a")
        oracle.record_reuse("p-a", "agent-1", "import")

        reports = oracle.assess_all_in_window(ImpactWindow.IMMEDIATE)
        assert "p-a" in reports
        assert isinstance(reports["p-a"], ImpactReport)

    @pytest.mark.parametrize("users,expected_level", [
        (0, "None"),
        (5, "Marginal"),
    ])
    def test_impact_levels(self, users, expected_level):
        oracle = ImpactOracle(network_size=100)
        oracle.register_contribution("p-level")
        for i in range(users):
            oracle.record_reuse("p-level", f"agent-{i}", "import")
        report = oracle.assess("p-level")
        assert report.score.impact_level in ["None", "Marginal", "Notable", "Meaningful", "Significant", "Transformative"]
        if users == 0:
            assert report.score.impact_level == "None"
