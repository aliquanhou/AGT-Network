"""
AGT Node — Credit Wallet

Experimental AGT Credit tracking.
v0.1: Simple credit accumulator — NOT a real token wallet.
Future: mapped to AGT Token on-chain.

Key distinction from a normal wallet:
- Credits are earned through VERIFIED intelligence contributions only
- Credits represent intellectual value creation, not speculation
- No transfer/mint/burn in v0.1
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CreditEntry:
    """A single credit transaction record"""
    entry_id: str
    amount: float
    proof_id: str  # Linked to the Intelligence Proof
    task_id: str
    type: str = "reward"  # reward | bonus | penalty
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CreditWallet:
    """
    AGT Credit Wallet — 实验积分钱包

    NOT a cryptocurrency wallet. Tracks earned AGT Credits from
    verified intelligence contributions.

    v0.1: Simple balance tracking.
    Future: on-chain AGT Token mapping.
    """

    node_id: str
    agent_id: str
    balance: float = 0.0
    entries: list[CreditEntry] = field(default_factory=list)

    def credit(self, amount: float, proof_id: str, task_id: str):
        """Receive AGT Credits for a contribution"""
        import uuid

        if amount <= 0:
            return

        entry = CreditEntry(
            entry_id=f"tx-{uuid.uuid4().hex[:8]}",
            amount=amount,
            proof_id=proof_id,
            task_id=task_id,
            type="reward",
        )
        self.entries.append(entry)
        self.balance += amount

        logger.info(
            f"[Wallet] Agent {self.agent_id}: +{amount:.1f} AGT Credit "
            f"(total: {self.balance:.1f}) — Proof: {proof_id}"
        )

    def status(self) -> dict:
        return {
            "node_id": self.node_id,
            "agent_id": self.agent_id,
            "balance": self.balance,
            "total_transactions": len(self.entries),
            "recent": [
                {
                    "amount": e.amount,
                    "proof_id": e.proof_id,
                    "task_id": e.task_id,
                    "timestamp": e.timestamp,
                }
                for e in self.entries[-5:]
            ],
        }
