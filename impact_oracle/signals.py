"""
Impact Oracle — Signal Types & Collectors (v0.3)

Impact measurement signals. These determine whether a contribution
produced real downstream value — not just whether it was completed.

Formula:
    Impact Score = Usage × Verification × Longevity × Diversity

Signal Tiers:
    Tier 1 (v0.3): On-chain — proof references, reuse, forks, validator citations
    Tier 2 (v0.5): External — GitHub stars, API calls, downloads
    Tier 3 (v1.0): Economic — market value, revenue, jobs created
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class SignalTier(str, Enum):
    ON_CHAIN = "on_chain"
    EXTERNAL = "external"
    ECONOMIC = "economic"


class SignalType(str, Enum):
    """Impact signal types"""
    PROOF_REFERENCE = "proof_reference"       # Another proof cites this output
    REUSE_COUNT = "reuse_count"               # Unique agents using this output
    FORK_COUNT = "fork_count"                 # Tasks derived from this output
    VALIDATOR_CITATION = "validator_citation"  # Validator references this
    GITHUB_STARS = "github_stars"             # External: stars on linked repo
    API_CALLS = "api_calls"                   # External: API invocations
    DOWNLOAD_COUNT = "download_count"         # External: package downloads
    ENTERPRISE_ADOPTION = "enterprise_adoption"  # External: enterprise usage
    MARKET_VALUE = "market_value"             # Economic: valuation
    REVENUE_GENERATED = "revenue_generated"   # Economic: attributed revenue


# Signal weights (protocol constants)
SIGNAL_WEIGHTS: dict[SignalType, float] = {
    # Tier 1: On-chain (v0.3)
    SignalType.PROOF_REFERENCE: 1.0,
    SignalType.REUSE_COUNT: 2.0,
    SignalType.FORK_COUNT: 3.0,
    SignalType.VALIDATOR_CITATION: 0.5,
    # Tier 2: External (v0.5+)
    SignalType.GITHUB_STARS: 1.5,
    SignalType.API_CALLS: 2.5,
    SignalType.DOWNLOAD_COUNT: 1.0,
    SignalType.ENTERPRISE_ADOPTION: 5.0,
    # Tier 3: Economic (v1.0+)
    SignalType.MARKET_VALUE: 4.0,
    SignalType.REVENUE_GENERATED: 5.0,
}

# Which tier each signal belongs to
SIGNAL_TIERS: dict[SignalType, SignalTier] = {
    SignalType.PROOF_REFERENCE: SignalTier.ON_CHAIN,
    SignalType.REUSE_COUNT: SignalTier.ON_CHAIN,
    SignalType.FORK_COUNT: SignalTier.ON_CHAIN,
    SignalType.VALIDATOR_CITATION: SignalTier.ON_CHAIN,
    SignalType.GITHUB_STARS: SignalTier.EXTERNAL,
    SignalType.API_CALLS: SignalTier.EXTERNAL,
    SignalType.DOWNLOAD_COUNT: SignalTier.EXTERNAL,
    SignalType.ENTERPRISE_ADOPTION: SignalTier.EXTERNAL,
    SignalType.MARKET_VALUE: SignalTier.ECONOMIC,
    SignalType.REVENUE_GENERATED: SignalTier.ECONOMIC,
}


@dataclass
class ImpactSignal:
    """A single recorded impact signal"""
    signal_type: SignalType
    value: float  # Count or metric value
    source_proof_id: str = ""  # Which proof generated this signal
    source_agent_id: str = ""  # Which agent generated this signal
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)

    @property
    def weight(self) -> float:
        return SIGNAL_WEIGHTS.get(self.signal_type, 1.0)

    @property
    def tier(self) -> SignalTier:
        return SIGNAL_TIERS.get(self.signal_type, SignalTier.ON_CHAIN)

    @property
    def weighted_value(self) -> float:
        return self.value * self.weight


class SignalCollector:
    """
    Collects impact signals for a given contribution (proof).

    Scans the network for references, reuses, forks, and citations
    of a specific contribution's output.
    """

    def __init__(self):
        self._signals: dict[str, list[ImpactSignal]] = {}  # proof_id → signals

    def record_signal(self, proof_id: str, signal: ImpactSignal):
        """Record a new impact signal for a proof"""
        if proof_id not in self._signals:
            self._signals[proof_id] = []
        self._signals[proof_id].append(signal)

    def record_reference(
        self,
        referenced_proof_id: str,
        referencing_proof_id: str,
        referencing_agent_id: str,
        depth: float = 1.0,
    ):
        """Record that a proof references another proof's output"""
        signal = ImpactSignal(
            signal_type=SignalType.PROOF_REFERENCE,
            value=1.0,
            source_proof_id=referencing_proof_id,
            source_agent_id=referencing_agent_id,
            metadata={"depth": depth},
        )
        self.record_signal(referenced_proof_id, signal)

    def record_reuse(
        self,
        proof_id: str,
        agent_id: str,
        reuse_type: str = "import",
    ):
        """Record that an agent reused a contribution's output"""
        signal = ImpactSignal(
            signal_type=SignalType.REUSE_COUNT,
            value=1.0,
            source_agent_id=agent_id,
            metadata={"reuse_type": reuse_type},
        )
        self.record_signal(proof_id, signal)

    def record_fork(
        self,
        original_proof_id: str,
        forked_task_id: str,
        agent_id: str,
    ):
        """Record that a task was derived/forked from this contribution"""
        signal = ImpactSignal(
            signal_type=SignalType.FORK_COUNT,
            value=1.0,
            source_proof_id=forked_task_id,
            source_agent_id=agent_id,
        )
        self.record_signal(original_proof_id, signal)

    def get_signals(
        self,
        proof_id: str,
        signal_type: Optional[SignalType] = None,
        tier: Optional[SignalTier] = None,
    ) -> list[ImpactSignal]:
        """Get signals for a proof, optionally filtered"""
        signals = self._signals.get(proof_id, [])
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        if tier:
            signals = [s for s in signals if s.tier == tier]
        return signals

    def get_unique_referencing_agents(self, proof_id: str) -> set[str]:
        """Get unique agents that have referenced this proof"""
        signals = self.get_signals(proof_id, SignalType.PROOF_REFERENCE)
        signals += self.get_signals(proof_id, SignalType.REUSE_COUNT)
        return {s.source_agent_id for s in signals if s.source_agent_id}

    def get_fork_count(self, proof_id: str) -> int:
        """Count of forks derived from this proof"""
        return len(self.get_signals(proof_id, SignalType.FORK_COUNT))

    def has_external_signals(self, proof_id: str) -> bool:
        """Check if any Tier 2+ signals exist"""
        return len(self.get_signals(proof_id, tier=SignalTier.EXTERNAL)) > 0

    def stats(self, proof_id: str) -> dict:
        """Summary statistics for a proof's signals"""
        all_signals = self.get_signals(proof_id)
        by_type = {}
        for s in all_signals:
            key = s.signal_type.value
            if key not in by_type:
                by_type[key] = {"count": 0, "weighted": 0.0}
            by_type[key]["count"] += 1
            by_type[key]["weighted"] += s.weighted_value

        return {
            "total_signals": len(all_signals),
            "unique_referencing_agents": len(self.get_unique_referencing_agents(proof_id)),
            "fork_count": self.get_fork_count(proof_id),
            "by_type": by_type,
        }
