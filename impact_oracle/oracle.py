"""
Impact Oracle — Main Oracle Engine (v0.3)

The Impact Oracle is the load-bearing economic defense of AGT v0.3.
It measures whether a contribution produced real downstream value.

Architecture:
    SignalCollector → ImpactScorer → EpochManager → ImpactOracle

Key capabilities:
- Collects usage/reuse/fork/citation signals
- Computes Impact = Usage × Verification × Longevity × Diversity
- Detects and penalizes self-referential (circular) impact
- Operates on epoch-delayed measurement (not real-time)
- Finalizes scores after 90 days (13 epochs)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .signals import SignalCollector, SignalType, ImpactSignal
from .scoring import ImpactScorer, ImpactScore
from .epoch import EpochManager, ImpactWindow

logger = logging.getLogger(__name__)


@dataclass
class ImpactReport:
    """Complete impact assessment for a contribution"""
    proof_id: str
    score: ImpactScore
    window: ImpactWindow
    signal_count: int
    unique_users: int
    fork_count: int
    is_circular: bool
    circular_references: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


class ImpactOracle:
    """
    Impact Oracle — measures real-world value of contributions.

    Usage:
        oracle = ImpactOracle(network_size=100)
        oracle.record_reference(proof_a, proof_b, agent_id)
        report = oracle.assess(proof_a)
    """

    def __init__(self, network_size: int = 100):
        self.collector = SignalCollector()
        self.scorer = ImpactScorer(self.collector)
        self.epochs = EpochManager()
        self.network_size = network_size

        # Reference graph for cycle detection: {referencing_proof: [referenced_proofs]}
        self._ref_graph: dict[str, list[str]] = {}

        # Start first epoch
        self.epochs.start_epoch()

    # ---- signal recording ----

    def record_reference(
        self,
        referencing_proof_id: str,
        referenced_proof_id: str,
        agent_id: str,
        depth: float = 1.0,
    ):
        """Record that one proof references another's output"""
        self.collector.record_reference(
            referenced_proof_id, referencing_proof_id, agent_id, depth
        )
        # Update reference graph
        if referencing_proof_id not in self._ref_graph:
            self._ref_graph[referencing_proof_id] = []
        self._ref_graph[referencing_proof_id].append(referenced_proof_id)

    def record_reuse(self, proof_id: str, agent_id: str, reuse_type: str = "import"):
        """Record that an agent reused a contribution"""
        self.collector.record_reuse(proof_id, agent_id, reuse_type)

    def record_fork(self, original_proof_id: str, forked_task_id: str, agent_id: str):
        """Record a derived/forked task"""
        self.collector.record_fork(original_proof_id, forked_task_id, agent_id)

    def register_contribution(self, proof_id: str):
        """Register a new contribution entering the impact window"""
        self.epochs.register_proof(proof_id)

    # ---- assessment ----

    def assess(self, proof_id: str) -> ImpactReport:
        """
        Produce a complete impact assessment for a contribution.

        Returns ImpactReport with score, window, and circularity check.
        """
        age = self.epochs.get_proof_age(proof_id)
        window = self.epochs.get_proof_window(proof_id)

        # Check for circular references
        circular_refs = self._detect_circular_references(proof_id)
        is_circular = len(circular_refs) > 0

        # Compute score
        score = self.scorer.compute(
            proof_id=proof_id,
            epoch_number=self.epochs.current_epoch,
            network_size=self.network_size,
            age_in_epochs=age,
        )

        # If circular references detected, apply penalty
        if is_circular:
            penalty = min(1.0, len(circular_refs) * 0.25)
            score.scaled_score *= (1.0 - penalty)
            score.raw_score *= (1.0 - penalty)

        # Build evidence
        signal_stats = self.collector.stats(proof_id)
        evidence = {
            "signals": signal_stats,
            "age_epochs": age,
            "window": window.value,
            "finalized": self.epochs.is_finalized(proof_id),
            "circular_penalty_applied": is_circular,
        }

        return ImpactReport(
            proof_id=proof_id,
            score=score,
            window=window,
            signal_count=signal_stats["total_signals"],
            unique_users=signal_stats["unique_referencing_agents"],
            fork_count=signal_stats["fork_count"],
            is_circular=is_circular,
            circular_references=circular_refs,
            evidence=evidence,
        )

    def assess_all_in_window(self, window: ImpactWindow) -> dict[str, ImpactReport]:
        """Assess all proofs in a given impact window"""
        proofs = self.epochs.get_proofs_in_window(window)
        return {pid: self.assess(pid) for pid in proofs}

    # ---- cycle detection ----

    def _detect_circular_references(self, start_proof_id: str, max_depth: int = 10) -> list[str]:
        """
        Detect self-referential impact (circular references).

        Uses DFS to find cycles in the reference graph.
        Returns list of proof_ids forming a cycle, empty if acyclic.

        Examples of circular impact:
            A → B → A           (2-cycle)
            A → B → C → A       (3-cycle)
            A → B → C → B       (self-loop with B)
        """
        visited = set()
        path = []
        cycles = []

        def dfs(node: str):
            if node in path:
                # Cycle found — extract the cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in self._ref_graph.get(node, []):
                if path and neighbor == start_proof_id and len(path) >= 2:
                    # Found a cycle back to start
                    cycles.append(path + [start_proof_id])
                    return
                dfs(neighbor)

            path.pop()

        dfs(start_proof_id)
        return cycles[0][:-1] if cycles else []

    def has_cycle(self, proof_id: str) -> bool:
        """Check if a proof participates in any reference cycle"""
        return len(self._detect_circular_references(proof_id)) > 0

    # ---- epoch management ----

    def advance_epoch(self):
        """End current epoch and start a new one"""
        self.epochs.end_epoch()
        # Score all proofs in immediate window before advancing
        self.assess_all_in_window(ImpactWindow.IMMEDIATE)
        self.epochs.start_epoch()

    def advance_epochs(self, n: int):
        """Fast-forward N epochs (for simulation/testing)"""
        for _ in range(n):
            self.advance_epoch()

    # ---- queries ----

    def get_impact_leaderboard(self, limit: int = 20) -> list[dict]:
        """Get top contributions by impact score"""
        all_proofs = list(self.epochs._proof_entry_epoch.keys())
        reports = [(pid, self.assess(pid)) for pid in all_proofs]
        reports.sort(key=lambda x: x[1].score.display_score, reverse=True)
        return [
            {
                "proof_id": pid,
                "display_score": r.score.display_score,
                "level": r.score.impact_level,
                "window": r.window.value,
                "unique_users": r.unique_users,
            }
            for pid, r in reports[:limit]
        ]

    def stats(self) -> dict:
        return {
            "epoch": self.epochs.stats(),
            "network_size": self.network_size,
            "tracked_proofs": len(self.epochs._proof_entry_epoch),
            "reference_graph_size": len(self._ref_graph),
        }
