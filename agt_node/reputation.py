"""
AGT Node — Agent Reputation System

Manages agent reputation scores that influence:
- Task assignment priority
- Reward multipliers
- Trust in the network

Reputation Model:
    Initial: 100
    High-quality contribution: +5  (score > 80)
    Normal completion: +1        (score >= 50)
    Failed: -2                    (score < 50)
    Malicious: -50               (validation fraud, spam, etc.)

Reputation affects:
    - Task eligibility (min reputation for high-value tasks)
    - Reward multiplier (high rep → bonus)
    - Network trust (visible in dashboard)
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
    """A single reputation change event"""
    event: ReputationEvent
    delta: float
    reason: str
    task_id: str = ""
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
    ) -> float:
        """
        Apply a reputation change event.

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
            new_score=self.score,
        )
        self.history.append(record)

        logger.info(
            f"[Reputation] Agent {self.agent_id}: "
            f"{old_score:.0f} → {self.score:.0f} ({delta:+.0f}, {event.value})"
        )

        return delta

    def apply_contribution_result(self, contribution_score: float, task_id: str):
        """
        Automatically determine and apply reputation change based on
        contribution score.
        """
        if contribution_score >= 80:
            return self.apply_event(
                ReputationEvent.HIGH_QUALITY,
                task_id=task_id,
                reason=f"High quality contribution (score: {contribution_score:.1f})",
            )
        elif contribution_score >= 50:
            return self.apply_event(
                ReputationEvent.NORMAL_COMPLETION,
                task_id=task_id,
                reason=f"Normal completion (score: {contribution_score:.1f})",
            )
        else:
            return self.apply_event(
                ReputationEvent.FAILED,
                task_id=task_id,
                reason=f"Failed contribution (score: {contribution_score:.1f})",
            )

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
