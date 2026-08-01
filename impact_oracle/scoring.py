"""
Impact Oracle — Scoring Engine (v0.3)

Impact Score formula:
    Impact = Usage × Verification × Longevity × Diversity

Where:
    Usage:       How many agents/systems use this output
    Verification: How many independent validators confirm its value
    Longevity:    How long it continues to produce value
    Diversity:    How many different ecosystems/domains use it

All factors normalized to [0, 1] range, then multiplied.
Raw Impact Score ∈ [0, 1], scaled to [0, 1000] for display.
"""

import math
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .signals import SignalCollector, SignalType, SignalTier, ImpactSignal

logger = logging.getLogger(__name__)

# Decay constant: λ=0.01 means ~63% of impact remains after 100 epochs (~2 years)
# At 7-day epochs: 100 epochs ≈ 700 days ≈ 2 years
DECAY_LAMBDA = 0.01

# Network size normalization base
NETWORK_SIZE_BASE = 100  # log10(100) = 2, so normalization = log10(N)/2


@dataclass
class ImpactScore:
    """Computed impact score for a contribution"""
    proof_id: str
    usage_factor: float       # [0, 1]
    verification_factor: float  # [0, 1]
    longevity_factor: float     # [0, 1] — decays over time
    diversity_factor: float     # [0, 1]

    raw_score: float = 0.0     # product × 1000
    scaled_score: float = 0.0  # network-size-normalized
    epoch_number: int = 0
    finalized: bool = False
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def display_score(self) -> float:
        """0-1000 scale for UI"""
        return round(self.scaled_score, 1)

    @property
    def impact_level(self) -> str:
        """Qualitative impact level"""
        s = self.display_score
        if s >= 800: return "Transformative"
        if s >= 500: return "Significant"
        if s >= 200: return "Meaningful"
        if s >= 50:  return "Notable"
        if s > 0:    return "Marginal"
        return "None"

    def to_dict(self) -> dict:
        return {
            "proof_id": self.proof_id,
            "factors": {
                "usage": round(self.usage_factor, 4),
                "verification": round(self.verification_factor, 4),
                "longevity": round(self.longevity_factor, 4),
                "diversity": round(self.diversity_factor, 4),
            },
            "scores": {
                "raw": round(self.raw_score, 2),
                "scaled": round(self.scaled_score, 2),
                "display": self.display_score,
                "level": self.impact_level,
            },
            "epoch": self.epoch_number,
            "finalized": self.finalized,
        }


class ImpactScorer:
    """
    Computes Impact Scores from signal data.

    Impact = Usage × Verification × Longevity × Diversity

    Each factor is normalized to [0, 1], then the product is
    scaled to [0, 1000] and normalized by network size.
    """

    def __init__(self, collector: SignalCollector):
        self.collector = collector

    def compute(
        self,
        proof_id: str,
        epoch_number: int = 0,
        network_size: int = 100,
        age_in_epochs: int = 1,
    ) -> ImpactScore:
        """
        Compute the impact score for a contribution.

        Args:
            proof_id: The contribution to score
            epoch_number: Current epoch
            network_size: Total number of agents in the network
            age_in_epochs: How many epochs since the contribution was made

        Returns:
            ImpactScore with all factors and final score
        """
        signals = self.collector.get_signals(proof_id)

        # ---- Usage Factor ----
        # How many unique agents reference this output
        unique_users = self.collector.get_unique_referencing_agents(proof_id)
        fork_count = self.collector.get_fork_count(proof_id)

        # Usage saturates logarithmically: 1 user=0.2, 10=0.5, 100=0.8, 1000=1.0
        usage_raw = len(unique_users) + fork_count * 2  # forks count double
        usage_factor = min(1.0, math.log10(max(1, usage_raw)) / math.log10(100))

        # ---- Verification Factor ----
        # How many independent validators have confirmed the value
        validator_signals = self.collector.get_signals(proof_id, SignalType.VALIDATOR_CITATION)
        unique_validators = len({s.source_agent_id for s in validator_signals if s.source_agent_id})
        verification_factor = min(1.0, unique_validators / 10.0)  # 10+ validators = full score

        # Bonus: external signals (Tier 2+) indicate real-world verification
        if self.collector.has_external_signals(proof_id):
            verification_factor = min(1.0, verification_factor + 0.2)

        # Floor: usage signals themselves imply partial verification (∃ users → ∃ value)
        if len(unique_users) > 0:
            verification_factor = max(0.1, verification_factor)

        # ---- Longevity Factor ----
        # How long the contribution continues to produce value
        # New contributions start at 1.0 and decay if no new signals
        recent_signals = [
            s for s in signals
            if age_in_epochs <= 90  # Within sustained window
        ]
        if len(recent_signals) > 0:
            # Active signals → longevity is high
            recency_ratio = len(recent_signals) / max(1, len(signals))
            longevity_factor = 0.5 + 0.5 * recency_ratio
        else:
            # No recent signals → decay
            longevity_factor = max(0.1, math.exp(-DECAY_LAMBDA * age_in_epochs))

        # ---- Diversity Factor ----
        # How many different types of signals
        signal_types = {s.signal_type for s in signals}
        unique_tiers = {s.tier for s in signals}
        diversity_factor = min(1.0,
            (len(signal_types) / len(SignalType)) * 0.5 +
            (len(unique_tiers) / 3) * 0.5
        )
        # Floor: even one signal type gives some diversity
        diversity_factor = max(0.1, diversity_factor)

        # ---- Compute Final Score ----
        raw = usage_factor * verification_factor * longevity_factor * diversity_factor
        scaled = raw * 1000.0

        # Network size normalization: larger networks should not inflate scores
        if network_size > NETWORK_SIZE_BASE:
            norm = math.log10(network_size) / math.log10(NETWORK_SIZE_BASE)
            scaled = scaled / norm

        return ImpactScore(
            proof_id=proof_id,
            usage_factor=usage_factor,
            verification_factor=verification_factor,
            longevity_factor=longevity_factor,
            diversity_factor=diversity_factor,
            raw_score=round(raw, 4),
            scaled_score=round(min(1000.0, scaled), 1),
            epoch_number=epoch_number,
            finalized=(age_in_epochs >= 13),  # ~90 days = 13 epochs
        )
