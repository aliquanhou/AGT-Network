"""
Impact Oracle — Epoch System (v0.3)

Epoch-based impact measurement to prevent real-time feedback loops.

Epoch: 7 days (configurable)
- Contributions completed in Epoch N-1 enter Impact Window at start of Epoch N
- Signal collectors gather references during Epoch N
- At end of Epoch N, Impact Scores for N-1 contributions are computed

Windows:
    Immediate:  0-7 days   (1 epoch)   — fast feedback
    Sustained:  7-90 days  (13 epochs) — proves lasting value
    Enduring:   90+ days               — legacy impact

After 13 epochs (~90 days), Impact Scores are finalized and sealed.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ImpactWindow(str, Enum):
    IMMEDIATE = "immediate"    # 0-7 days
    SUSTAINED = "sustained"    # 7-90 days
    ENDURING = "enduring"      # 90+ days


# Window boundaries in epochs (1 epoch = 7 days)
WINDOW_BOUNDARIES = {
    ImpactWindow.IMMEDIATE: (0, 1),     # 0-1 epochs
    ImpactWindow.SUSTAINED: (1, 13),    # 1-13 epochs
    ImpactWindow.ENDURING: (13, None),  # 13+ epochs
}


@dataclass
class EpochRecord:
    """Record of a single epoch's impact state"""
    epoch_number: int
    started_at: str
    ended_at: str = ""
    contributions_entering: int = 0  # New proofs entering impact window
    contributions_scored: int = 0    # Proofs scored this epoch
    contributions_finalized: int = 0 # Proofs reaching enduring window
    total_signals_collected: int = 0
    active: bool = True


class EpochManager:
    """
    Manages the epoch lifecycle for impact measurement.

    Epochs create a delayed measurement window that prevents
    real-time feedback loops in the impact system.
    """

    def __init__(self, epoch_duration_seconds: int = 7 * 24 * 3600):
        self.epoch_duration = epoch_duration_seconds  # Default: 7 days
        self.current_epoch: int = 0
        self.epochs: list[EpochRecord] = []

        # Track which epoch each proof entered the impact window
        self._proof_entry_epoch: dict[str, int] = {}  # proof_id → epoch_number

    # ---- epoch lifecycle ----

    def start_epoch(self) -> EpochRecord:
        """Start a new epoch"""
        self.current_epoch += 1
        record = EpochRecord(
            epoch_number=self.current_epoch,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self.epochs.append(record)
        logger.info(f"[Epoch] Epoch {self.current_epoch} started")
        return record

    def end_epoch(self):
        """End the current epoch — triggers scoring"""
        if self.epochs:
            self.epochs[-1].ended_at = datetime.now(timezone.utc).isoformat()
            self.epochs[-1].active = False
        logger.info(f"[Epoch] Epoch {self.current_epoch} ended")

    # ---- proof tracking ----

    def register_proof(self, proof_id: str):
        """Register a new proof entering the impact window at current epoch"""
        self._proof_entry_epoch[proof_id] = self.current_epoch
        if self.epochs:
            self.epochs[-1].contributions_entering += 1

    def get_proof_age(self, proof_id: str) -> int:
        """How many epochs old is this proof? (0 = current epoch)"""
        entry = self._proof_entry_epoch.get(proof_id)
        if entry is None:
            return 0
        return self.current_epoch - entry

    def get_proof_window(self, proof_id: str) -> ImpactWindow:
        """Which impact window is this proof currently in?"""
        age = self.get_proof_age(proof_id)
        if age <= 1:
            return ImpactWindow.IMMEDIATE
        elif age <= 13:
            return ImpactWindow.SUSTAINED
        else:
            return ImpactWindow.ENDURING

    def is_finalized(self, proof_id: str) -> bool:
        """Has this proof's impact been finalized?"""
        return self.get_proof_window(proof_id) == ImpactWindow.ENDURING

    def get_proofs_in_window(self, window: ImpactWindow) -> list[str]:
        """Get all proofs in a given impact window"""
        low, high = WINDOW_BOUNDARIES[window]
        result = []
        for proof_id, entry_epoch in self._proof_entry_epoch.items():
            age = self.current_epoch - entry_epoch
            if high is None:
                if age >= low:
                    result.append(proof_id)
            else:
                if low <= age <= high:
                    result.append(proof_id)
        return result

    # ---- stats ----

    def stats(self) -> dict:
        return {
            "current_epoch": self.current_epoch,
            "total_epochs": len(self.epochs),
            "proofs_tracked": len(self._proof_entry_epoch),
            "by_window": {
                "immediate": len(self.get_proofs_in_window(ImpactWindow.IMMEDIATE)),
                "sustained": len(self.get_proofs_in_window(ImpactWindow.SUSTAINED)),
                "enduring": len(self.get_proofs_in_window(ImpactWindow.ENDURING)),
            },
        }

    # ---- testing helpers ----

    def advance_epochs(self, n: int):
        """Fast-forward N epochs (for simulation/testing only)"""
        for _ in range(n):
            self.end_epoch()
            self.start_epoch()
