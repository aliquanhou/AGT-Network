"""
AGT Economy — Emission Interface (v0.1 STUB)

Future: Controls AGT Token emission schedule.
- Initial supply
- Inflation rate
- Halving events
- Burn mechanism

v0.1: Only defines the interface. No tokens are emitted.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class EmissionSchedule(Protocol):
    """Protocol for future emission schedules"""

    def get_current_supply(self) -> float:
        """Total circulating supply"""
        ...

    def get_emission_rate(self) -> float:
        """Current emission rate (tokens per block/epoch)"""
        ...

    def get_next_halving(self) -> datetime:
        """Timestamp of next halving event"""
        ...


@dataclass
class EmissionConfig:
    """
    Future emission configuration.

    v0.1: Placeholder values — not active.
    v0.5+: Used by the emission engine for AGT Token.
    """
    initial_supply: float = 0.0
    max_supply: float = 1_000_000_000.0  # 1 billion
    base_emission_rate: float = 100.0  # tokens per epoch
    halving_epochs: int = 210_000  # epochs between halvings
    target_block_time: float = 15.0  # seconds

    def get_epochs_per_year(self) -> float:
        """Calculate epochs per year based on target block time"""
        seconds_per_year = 365.25 * 24 * 3600
        return seconds_per_year / self.target_block_time
