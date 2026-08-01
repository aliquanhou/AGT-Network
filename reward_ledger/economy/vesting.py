"""
AGT Economy — Vesting Interface (v0.1 STUB)

Future: Manages token vesting schedules.
- Agent reward vesting
- Validator stake vesting
- Founder vesting (long-term alignment)
- Community treasury release

v0.1: Only defines the interface. No vesting in effect.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Protocol


class VestingCliff(Enum):
    """Vesting cliff types"""
    NONE = "none"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FOUR_YEARS = "4y"


class VestingSchedule(Protocol):
    """Protocol for future vesting schedules"""

    def get_vested_amount(self, timestamp: datetime) -> float:
        """Amount vested at given timestamp"""
        ...

    def get_unlocked_amount(self, timestamp: datetime) -> float:
        """Amount unlocked (vested + cliff passed)"""
        ...

    def get_remaining_locked(self, timestamp: datetime) -> float:
        """Amount still locked"""
        ...


@dataclass
class VestingConfig:
    """
    Future vesting configuration.

    v0.1: Placeholder — not active.
    v0.5+:
    - Agent rewards: 30-day linear vesting (prevents gaming)
    - Validator stakes: 90-day linear vesting
    - Founder allocation: 4-year linear vesting with 1-year cliff
    """
    agent_reward_vesting_days: int = 30
    validator_vesting_days: int = 90
    founder_vesting_years: int = 4
    founder_cliff_years: int = 1
    treasury_vesting_years: int = 10  # Slow release for long-term sustainability

    def get_agent_vesting_end(self, start: datetime) -> datetime:
        return start + timedelta(days=self.agent_reward_vesting_days)

    def get_founder_vesting_end(self, start: datetime) -> datetime:
        return start + timedelta(days=self.founder_vesting_years * 365)
