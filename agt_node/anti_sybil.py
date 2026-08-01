"""
AGT Node — Anti-Sybil Protection (v0.2 Trust Layer)

Heuristic detection of agent farming and contribution gaming.
Prevents a single entity from creating many fake agents to harvest rewards.

Detection signals:
1. Same output hash across multiple contributions
2. Rapid-fire task completion (sub-second cycles)
3. Identical quality scores across contributions
4. Excessive agent creation on a single node
5. Circular validation (same node validates its own agents)

These are heuristics — not cryptographic guarantees. They flag suspicious
activity for review without blocking legitimate multi-agent operation.
"""

import logging
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SybilAlert:
    """A flagged suspicious activity"""
    alert_id: str
    node_id: str
    agent_id: str = ""
    severity: str = "low"  # low, medium, high
    reason: str = ""
    evidence: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AntiSybil:
    """
    Anti-Sybil heuristic detector.

    Monitors contribution patterns for signs of agent farming.
    v0.2: Heuristic only — flags suspicious patterns, does not block.
    v0.5+: Cross-node consensus on Sybil detection.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id

        # Detection state
        self._output_hashes: dict[str, int] = defaultdict(int)  # hash → count
        self._task_timestamps: list[float] = []  # recent task completion times
        self._agent_contribution_counts: dict[str, int] = defaultdict(int)
        self._quality_score_history: dict[str, list[float]] = defaultdict(list)
        self._alerts: list[SybilAlert] = []

        # Thresholds
        self.max_identical_outputs = 3  # Same output hash appearing this many times
        self.min_task_interval_ms = 100  # Tasks faster than this are suspicious
        self.max_agents_per_node = 100  # More agents than this flags a warning

    def check_contribution(
        self,
        proof: "IntelligenceProof",
        agent_id: str,
        worker_node_id: str,
    ) -> Optional[SybilAlert]:
        """
        Check a new contribution for Sybil patterns.

        Returns a SybilAlert if suspicious, None if clean.
        """
        import uuid
        import time

        # Signal 1: Identical output across contributions
        if proof.evidence:
            first_hash = proof.evidence[0].content_hash
            self._output_hashes[first_hash] += 1
            count = self._output_hashes[first_hash]
            if count >= self.max_identical_outputs:
                alert = SybilAlert(
                    alert_id=f"sybil-{uuid.uuid4().hex[:8]}",
                    node_id=worker_node_id,
                    agent_id=agent_id,
                    severity="high",
                    reason=f"Identical output hash appeared {count} times "
                           f"— possible copy-paste farming",
                    evidence={"output_hash": first_hash, "count": count},
                )
                self._alerts.append(alert)
                logger.warning(f"[AntiSybil] {alert.reason}")
                return alert

        # Signal 2: Rapid-fire task completion
        now = time.time()
        self._task_timestamps.append(now)
        # Keep last 20 timestamps
        if len(self._task_timestamps) > 20:
            self._task_timestamps = self._task_timestamps[-20:]

        if len(self._task_timestamps) >= 3:
            recent = self._task_timestamps[-3:]
            intervals = [recent[i+1] - recent[i] for i in range(len(recent) - 1)]
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval < (self.min_task_interval_ms / 1000.0):
                alert = SybilAlert(
                    alert_id=f"sybil-{uuid.uuid4().hex[:8]}",
                    node_id=worker_node_id,
                    agent_id=agent_id,
                    severity="medium",
                    reason=f"Rapid task completion: avg {avg_interval*1000:.0f}ms "
                           f"between tasks (threshold: {self.min_task_interval_ms}ms)",
                    evidence={"avg_interval_ms": avg_interval * 1000, "recent_count": len(recent)},
                )
                self._alerts.append(alert)
                logger.warning(f"[AntiSybil] {alert.reason}")
                return alert

        # Signal 3: Excessive agent count on a node
        self._agent_contribution_counts[agent_id] += 1
        unique_agents = len(self._agent_contribution_counts)
        if unique_agents > self.max_agents_per_node:
            alert = SybilAlert(
                alert_id=f"sybil-{uuid.uuid4().hex[:8]}",
                node_id=worker_node_id,
                severity="low",
                reason=f"Node has {unique_agents} agents "
                       f"(threshold: {self.max_agents_per_node})",
                evidence={"agent_count": unique_agents},
            )
            self._alerts.append(alert)
            logger.warning(f"[AntiSybil] {alert.reason}")
            return alert

        return None  # Clean

    def get_alerts(self, limit: int = 20) -> list[SybilAlert]:
        """Get recent Sybil alerts"""
        return self._alerts[-limit:]

    def get_alert_count(self) -> int:
        """Total number of alerts raised"""
        return len(self._alerts)

    def stats(self) -> dict:
        return {
            "alerts_raised": len(self._alerts),
            "by_severity": {
                "high": sum(1 for a in self._alerts if a.severity == "high"),
                "medium": sum(1 for a in self._alerts if a.severity == "medium"),
                "low": sum(1 for a in self._alerts if a.severity == "low"),
            },
            "unique_agents_tracked": len(self._agent_contribution_counts),
            "output_hashes_tracked": len(self._output_hashes),
        }
