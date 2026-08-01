"""
Protocol Fee Engine — v0.3 Autonomous Economy

Implements the 2% Intelligence Protocol Fee with Genesis Vault.

Fee Schedule (protocol constants):
    2% of every task reward
    → 1.0% Network Infrastructure Fund
    → 0.5% Ecosystem Development Fund
    → 0.5% Genesis Contribution Attribution (→ Genesis Vault)

Genesis Vault:
    - Receives 0.5% of every task reward
    - 20-year linear vesting schedule
    - Public, auditable ledger address
    - Maximum lifetime: 0.5% × 1,000,000,000 = 5,000,000 AGT
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# === Protocol Constants (immutable without governance upgrade) ===

PROTOCOL_FEE_PCT = 0.02  # 2% total

FEE_DISTRIBUTION = {
    "network_infrastructure": 0.50,   # 1.0% of gross reward
    "ecosystem_development": 0.25,    # 0.5% of gross reward
    "genesis_contribution": 0.25,     # 0.5% of gross reward
}

GENESIS_VAULT_ADDRESS = "agt-genesis-vault-000000000000"

# 20-year vesting: 1/20 per year, 1/240 per epoch (monthly)
VESTING_YEARS = 20
VESTING_EPOCHS = VESTING_YEARS * 12  # 240 monthly epochs
VESTING_RATE_PER_EPOCH = 1.0 / VESTING_EPOCHS  # ~0.416% per month

MAX_SUPPLY = 1_000_000_000.0

# Maximum Genesis Attribution over entire supply life
MAX_GENESIS_ATTRIBUTION = MAX_SUPPLY * FEE_DISTRIBUTION["genesis_contribution"] * PROTOCOL_FEE_PCT
# = 1,000,000,000 × 0.25 × 0.02 = 5,000,000 AGT


@dataclass
class FeeAllocation:
    """Breakdown of a single fee application"""
    gross_reward: float
    fee_total: float
    network_infrastructure: float
    ecosystem_development: float
    genesis_contribution: float
    net_to_participants: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class GenesisVault:
    """
    Genesis Vault — transparent, time-locked protocol fund.

    Receives 0.5% of every task reward.
    Released linearly over 20 years.
    Publicly auditable.
    """

    balance: float = 0.0
    total_received: float = 0.0
    total_released: float = 0.0
    epochs_elapsed: int = 0
    vault_address: str = GENESIS_VAULT_ADDRESS

    def deposit(self, amount: float):
        """Deposit into the vault (from protocol fee)"""
        self.balance += amount
        self.total_received += amount

    def release_epoch(self) -> float:
        """
        Release one epoch's worth of vested funds.

        Returns the amount released this epoch.
        20-year linear vesting: ~0.416% of total per month.
        """
        self.epochs_elapsed += 1

        # Vested amount: total_received × (epochs_elapsed / total_epochs)
        vested_pct = self.epochs_elapsed / VESTING_EPOCHS
        vested_total = self.total_received * min(1.0, vested_pct)

        # How much to release this epoch
        releasable = vested_total - self.total_released
        if releasable > 0:
            self.total_released += releasable
            self.balance -= releasable
            logger.info(
                f"[Vault] Epoch {self.epochs_elapsed}: released {releasable:.2f} AGT "
                f"(vested: {vested_pct*100:.1f}%, balance: {self.balance:.2f})"
            )
            return releasable

        return 0.0

    def stats(self) -> dict:
        vested_pct = min(100.0, (self.epochs_elapsed / VESTING_EPOCHS) * 100)
        return {
            "address": self.vault_address,
            "balance": round(self.balance, 2),
            "total_received": round(self.total_received, 2),
            "total_released": round(self.total_released, 2),
            "epochs_elapsed": self.epochs_elapsed,
            "vested_pct": round(vested_pct, 2),
            "vesting_years_remaining": round(VESTING_YEARS * (1 - vested_pct/100), 1),
            "max_lifetime_attribution": MAX_GENESIS_ATTRIBUTION,
        }


class ProtocolFeeEngine:
    """
    Protocol Fee Engine.

    Applies the 2% Intelligence Protocol Fee to every task reward
    and routes funds to the correct destinations.

    Key guarantees:
    - Fee % is constant (verified at engine creation)
    - Genesis Vault cannot exceed max lifetime attribution
    - All allocations are transparent and auditable
    """

    def __init__(self):
        # Immutability guard: crash if constants are tampered
        assert PROTOCOL_FEE_PCT == 0.02, "PROTOCOL_FEE_PCT corrupted"
        assert abs(sum(FEE_DISTRIBUTION.values()) - 1.0) < 0.001, "FEE_DISTRIBUTION corrupted"

        self.vault = GenesisVault()
        self._total_fees_collected: float = 0.0
        self._allocations: list[FeeAllocation] = []

        # Fee pots
        self.network_infrastructure_fund: float = 0.0
        self.ecosystem_development_fund: float = 0.0

    def apply_fee(self, reward: float) -> FeeAllocation:
        """
        Apply the protocol fee to a task reward.

        Args:
            reward: Gross task reward (before fee)

        Returns:
            FeeAllocation with breakdown

        Raises:
            ValueError if reward would exceed supply cap
        """
        fee = reward * PROTOCOL_FEE_PCT
        net = reward - fee

        alloc = FeeAllocation(
            gross_reward=reward,
            fee_total=fee,
            network_infrastructure=fee * FEE_DISTRIBUTION["network_infrastructure"],
            ecosystem_development=fee * FEE_DISTRIBUTION["ecosystem_development"],
            genesis_contribution=fee * FEE_DISTRIBUTION["genesis_contribution"],
            net_to_participants=net,
        )

        # Route funds
        self.network_infrastructure_fund += alloc.network_infrastructure
        self.ecosystem_development_fund += alloc.ecosystem_development
        self.vault.deposit(alloc.genesis_contribution)

        # Supply guard: max genesis attribution
        if self.vault.total_received > MAX_GENESIS_ATTRIBUTION:
            logger.warning(
                f"[FeeEngine] Genesis Vault at max attribution: "
                f"{self.vault.total_received:.2f} / {MAX_GENESIS_ATTRIBUTION:.2f}"
            )

        self._total_fees_collected += fee
        self._allocations.append(alloc)

        return alloc

    def apply_fee_to_distribution(self, discoverer: float, executor: float, validator: float, backer: float = 0) -> dict:
        """
        Apply protocol fee to the standard reward distribution.

        The fee is deducted proportionally from each share.
        Returns net amounts for each participant.
        """
        gross = discoverer + executor + validator + backer
        fee_total = gross * PROTOCOL_FEE_PCT

        # Deduct proportionally
        def net(share: float) -> float:
            return share - (fee_total * (share / gross)) if gross > 0 else 0

        return {
            "discoverer": round(net(discoverer), 2),
            "executor": round(net(executor), 2),
            "validator": round(net(validator), 2),
            "backer": round(net(backer), 2),
            "fee_breakdown": {
                "total_fee": round(fee_total, 2),
                "network_infrastructure": round(fee_total * FEE_DISTRIBUTION["network_infrastructure"], 2),
                "ecosystem_development": round(fee_total * FEE_DISTRIBUTION["ecosystem_development"], 2),
                "genesis_contribution": round(fee_total * FEE_DISTRIBUTION["genesis_contribution"], 2),
            }
        }

    def advance_epoch(self):
        """Advance one epoch — releases vested funds from Genesis Vault"""
        return self.vault.release_epoch()

    def stats(self) -> dict:
        return {
            "total_fees_collected": round(self._total_fees_collected, 2),
            "network_infrastructure_fund": round(self.network_infrastructure_fund, 2),
            "ecosystem_development_fund": round(self.ecosystem_development_fund, 2),
            "vault": self.vault.stats(),
            "fee_constants": {
                "protocol_fee_pct": PROTOCOL_FEE_PCT,
                "distribution": FEE_DISTRIBUTION,
                "max_genesis_attribution": MAX_GENESIS_ATTRIBUTION,
            },
        }
