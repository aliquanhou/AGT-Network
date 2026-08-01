"""
AGT Economy — Allocation Interface (v0.1 STUB)

Future: Defines how AGT Tokens are allocated across:
- Agent reward pool
- Validator incentive pool
- Network operation fund
- Community treasury
- Founder recognition (non-transferable)

v0.1: Only defines the interface. No tokens are allocated.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol


class AllocationPolicy(Protocol):
    """Protocol for future allocation policies"""

    def get_agent_reward_share(self) -> float:
        """Percentage of emissions allocated to agent rewards"""
        ...

    def get_validator_share(self) -> float:
        """Percentage allocated to validators"""
        ...

    def get_treasury_share(self) -> float:
        """Percentage allocated to community treasury"""
        ...


@dataclass
class AllocationConfig:
    """
    Future allocation configuration.

    v0.1: Placeholder values — not active.
    v0.5+: Used by the emission engine.
    """
    agent_reward_pool: float = 0.50  # 50%
    validator_pool: float = 0.20     # 20%
    network_operations: float = 0.15  # 15%
    community_treasury: float = 0.10  # 10%
    founder_recognition: float = 0.05  # 5% (non-transferable)

    def validate(self) -> bool:
        """Validate that allocations sum to 1.0"""
        total = (
            self.agent_reward_pool
            + self.validator_pool
            + self.network_operations
            + self.community_treasury
            + self.founder_recognition
        )
        return abs(total - 1.0) < 0.001
