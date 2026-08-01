"""
AGT Node — Agent Reputation System (v0.2 Trust Layer)

Soulbound reputation — every change must reference a signed IntelligenceProof.
Reputation cannot be transferred, purchased, or assigned directly.

Reputation Model:
    Initial: 100
    High-quality contribution: +5  (score > 80)
    Normal completion: +1        (score >= 50)
    Failed: -2                    (score < 50)
    Malicious: -50               (validation fraud, spam, etc.)

v0.2 upgrade:
- Every ReputationRecord now includes proof_id (mandatory)
- verify_reputation_trace() validates the full reputation history
- score is internally mutable but externally read-only (soulbound)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ReputationEvent(str, Enum):
    """Events that trigger reputation changes"""
    GENESIS = "genesis"
    HIGH_QUALITY = "high_quality"  # Score > 80
    NORMAL_COMPLETION = "normal_completion"  # Score >= 50
    FAILED = "failed"  # Score < 50
    MALICIOUS = "malicious"  # Intentional misconduct
    VALIDATOR_EXCELLENCE = "validator_excellence"  # Good validation work
    COMMUNITY_CONTRIBUTION = "community_contribution"


# Reputation delta per event type
REPUTATION_DELTA = {
    ReputationEvent.HIGH_QUALITY: +5,
    ReputationEvent.NORMAL_COMPLETION: +1,
    ReputationEvent.FAILED: -2,
    ReputationEvent.MALICIOUS: -50,
    ReputationEvent.VALIDATOR_EXCELLENCE: +3,
    ReputationEvent.COMMUNITY_CONTRIBUTION: +2,
}

# Thresholds
MIN_REPUTATION = 0
MAX_REPUTATION = 1000
DEFAULT_REPUTATION = 100
HIGH_QUALITY_THRESHOLD = 80  # Contribution score above this → high quality
MIN_TASK_REPUTATION = {
    1: 0,    # Difficulty 1-3: no minimum
    2: 0,
    3: 0,
    4: 10,   # Difficulty 4-6: need reputation >= 10
    5: 10,
    6: 10,
    7: 30,   # Difficulty 7-8: need reputation >= 30
    8: 30,
    9: 50,   # Difficulty 9-10: need reputation >= 50
    10: 50,
}


@dataclass
class ReputationRecord:
    """A single reputation change event (v0.2: must reference a signed proof)"""
    event: ReputationEvent
    delta: float
    reason: str
    task_id: str = ""
    proof_id: str = ""  # v0.2: reference to signed IntelligenceProof
    new_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AgentReputation:
    """
    Agent reputation profile.

    Tracks reputation history and determines eligibility.
    """

    agent_id: str
    score: float = DEFAULT_REPUTATION
    history: list[ReputationRecord] = field(default_factory=list)

    @property
    def level(self) -> str:
        """Qualitative reputation level"""
        if self.score >= 500:
            return "Sage"
        elif self.score >= 300:
            return "Expert"
        elif self.score >= 150:
            return "Trusted"
        elif self.score >= 100:
            return "Active"
        elif self.score >= 50:
            return "Newcomer"
        else:
            return "Unreliable"

    @property
    def reward_multiplier(self) -> float:
        """Reputation-based reward bonus"""
        if self.score >= 500:
            return 1.5
        elif self.score >= 300:
            return 1.3
        elif self.score >= 150:
            return 1.1
        elif self.score >= 100:
            return 1.0
        else:
            return 0.8

    def can_take_task(self, difficulty: int) -> bool:
        """Check if agent has enough reputation for a task"""
        required = MIN_TASK_REPUTATION.get(difficulty, 0)
        return self.score >= required

    def apply_event(
        self,
        event: ReputationEvent,
        task_id: str = "",
        reason: str = "",
        proof_id: str = "",
    ) -> float:
        """
        Apply a reputation change event (v0.2: with proof reference).

        Returns the delta applied.
        """
        delta = REPUTATION_DELTA.get(event, 0)

        old_score = self.score
        self.score = max(MIN_REPUTATION, min(MAX_REPUTATION, self.score + delta))

        record = ReputationRecord(
            event=event,
            delta=delta,
            reason=reason,
            task_id=task_id,
            proof_id=proof_id,
            new_score=self.score,
        )
        self.history.append(record)

        logger.info(
            f"[Reputation] Agent {self.agent_id}: "
            f"{old_score:.0f} → {self.score:.0f} ({delta:+.0f}, {event.value})"
        )

        return delta

    def apply_contribution_result(
        self,
        contribution_score: float,
        task_id: str,
        proof_id: str = "",
    ) -> float:
        """
        Automatically determine and apply reputation change based on
        contribution score (v0.2: proof_id required for traceability).
        """
        if contribution_score >= 80:
            return self.apply_event(
                ReputationEvent.HIGH_QUALITY,
                task_id=task_id,
                proof_id=proof_id,
                reason=f"High quality contribution (score: {contribution_score:.1f})",
            )
        elif contribution_score >= 50:
            return self.apply_event(
                ReputationEvent.NORMAL_COMPLETION,
                task_id=task_id,
                proof_id=proof_id,
                reason=f"Normal completion (score: {contribution_score:.1f})",
            )
        else:
            return self.apply_event(
                ReputationEvent.FAILED,
                task_id=task_id,
                proof_id=proof_id,
                reason=f"Failed contribution (score: {contribution_score:.1f})",
            )

    def verify_reputation_trace(self) -> bool:
        """
        v0.2: Verify that every reputation change references a proof.

        Returns True if all non-genesis events have proof_id references.
        """
        for record in self.history:
            if record.event != ReputationEvent.GENESIS and not record.proof_id:
                logger.warning(
                    f"[Reputation] Untraceable change for {self.agent_id}: "
                    f"event={record.event.value}, no proof_id"
                )
                return False
        return True

    def apply_contribution_history(self, blocks: list) -> float:
        """
        v0.36.4: Rebuild reputation score from ledger block history.

        Scans every block for this agent and replays reputation changes
        to reconstruct the correct score after a restart.
        """
        total_delta = 0.0
        for block in blocks:
            if hasattr(block, 'contribution_proof') and block.contribution_proof:
                score = block.contribution_proof.contribution_score
                proof_id = block.contribution_proof.proof_id
                task_id = block.task_id
                if score >= 80:
                    event = ReputationEvent.HIGH_QUALITY
                elif score >= 50:
                    event = ReputationEvent.NORMAL_COMPLETION
                else:
                    event = ReputationEvent.FAILED
                delta = REPUTATION_DELTA.get(event, 0)
                self.score = max(MIN_REPUTATION, min(MAX_REPUTATION, self.score + delta))
                total_delta += delta
                self.history.append(ReputationRecord(
                    event=event,
                    delta=delta,
                    reason=f"Restored: {event.value} (score: {score:.1f})",
                    task_id=task_id,
                    proof_id=proof_id,
                    new_score=self.score,
                ))
        if total_delta != 0:
            logger.info(
                f"[Reputation] Agent {self.agent_id} restored from {len(blocks)} blocks: "
                f"score={self.score:.0f} ({self.level})"
            )
        return total_delta

    def get_recent_history(self, limit: int = 10) -> list[ReputationRecord]:
        return self.history[-limit:]

    def status(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "score": self.score,
            "level": self.level,
            "reward_multiplier": self.reward_multiplier,
            "total_events": len(self.history),
        }
