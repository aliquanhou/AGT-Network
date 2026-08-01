"""
Intelligence Ledger — 智能贡献账本

Records the history of Agent intelligence contributions.
This is NOT a cryptocurrency ledger — it tracks intellectual value creation.
Future: AGT Token will be a mapping over this ledger.

Block Structure:
    {
        block_id,
        index,
        contribution_proof,
        reputation_change,
        reward_credit,
        previous_hash,
        timestamp,
        node_id,
        agent_id
    }
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from poi_consensus.intelligence_proof import IntelligenceProof

logger = logging.getLogger(__name__)


@dataclass
class LedgerBlock:
    """
    A single block in the Intelligence Ledger.

    Each block records one verified intelligence contribution.
    Blocks are chained via previous_hash for tamper evidence.
    """

    block_id: str
    index: int
    node_id: str
    agent_id: str
    task_id: str

    # Core payload
    contribution_proof: IntelligenceProof
    reputation_change: float = 0.0  # Delta applied to agent reputation
    reward_credit: float = 0.0  # AGT Credit awarded

    # Chain integrity
    previous_hash: str = ""
    block_hash: str = ""

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_hash(self) -> str:
        """SHA-256 hash of block content for tamper detection"""
        core = {
            "block_id": self.block_id,
            "index": self.index,
            "node_id": self.node_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "proof_id": self.contribution_proof.proof_id if self.contribution_proof else "",
            "contribution_score": (
                self.contribution_proof.contribution_score
                if self.contribution_proof
                else 0
            ),
            "reputation_change": self.reputation_change,
            "reward_credit": self.reward_credit,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
        }
        serialized = json.dumps(core, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "block_id": self.block_id,
            "index": self.index,
            "node_id": self.node_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "proof": self.contribution_proof.to_dict() if self.contribution_proof else None,
            "reputation_change": self.reputation_change,
            "reward_credit": self.reward_credit,
            "previous_hash": self.previous_hash,
            "block_hash": self.block_hash,
            "timestamp": self.timestamp,
        }


class IntelligenceLedger:
    """
    Intelligence Ledger — the core ledger of the AGT Network.

    Records every verified intelligence contribution.
    Uses a hash chain for integrity (not a blockchain — v0.1).

    Key distinction:
        NOT a wallet: doesn't track balances.
        IS a history: each block records value creation.

    Future: on-chain AGT Token maps to these entries.
    """

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.blocks: list[LedgerBlock] = []
        self._file_path = os.path.join(data_dir, "intelligence_ledger.json")

        # Stats
        self.total_credit_issued: float = 0.0
        self.total_contributions: int = 0

    # ---- lifecycle ----

    def load(self):
        """Load ledger from disk"""
        try:
            if os.path.exists(self._file_path):
                with open(self._file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.total_credit_issued = data.get("total_credit_issued", 0.0)
                self.total_contributions = data.get("total_contributions", 0)
                logger.info(
                    f"[Ledger] Loaded: {self.total_contributions} blocks, "
                    f"{self.total_credit_issued} AGT Credit issued"
                )
        except Exception as e:
            logger.warning(f"[Ledger] Could not load: {e}")
            self.blocks = []

    def save(self):
        """Persist ledger metadata to disk"""
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            metadata = {
                "total_credit_issued": self.total_credit_issued,
                "total_contributions": self.total_contributions,
                "last_block_hash": self.blocks[-1].block_hash if self.blocks else "",
                "block_count": len(self.blocks),
            }
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[Ledger] Could not save: {e}")

    # ---- block creation ----

    def record_contribution(
        self,
        proof: IntelligenceProof,
        reputation_change: float,
        reward_credit: float,
        node_id: str,
        agent_id: str,
    ) -> LedgerBlock:
        """
        Record a verified intelligence contribution as a new block.

        This is the core ledger operation: transforming an
        Intelligence Proof into a permanent record.
        """
        import uuid

        index = len(self.blocks)
        previous_hash = self.blocks[-1].block_hash if self.blocks else "genesis"

        block = LedgerBlock(
            block_id=f"blk-{uuid.uuid4().hex[:8]}",
            index=index,
            node_id=node_id,
            agent_id=agent_id,
            task_id=proof.task_id,
            contribution_proof=proof,
            reputation_change=reputation_change,
            reward_credit=reward_credit,
            previous_hash=previous_hash,
        )

        block.block_hash = block.compute_hash()
        self.blocks.append(block)

        self.total_contributions += 1
        self.total_credit_issued += reward_credit

        logger.info(
            f"[Ledger] Block {block.index} created: "
            f"Agent={agent_id}, "
            f"Reward={reward_credit:.1f} AGT Credit, "
            f"Rep Δ={reputation_change:+.1f}"
        )

        self.save()
        return block

    # ---- queries ----

    def get_blocks_by_agent(self, agent_id: str) -> list[LedgerBlock]:
        """Get all blocks for a specific agent"""
        return [b for b in self.blocks if b.agent_id == agent_id]

    def get_blocks_by_node(self, node_id: str) -> list[LedgerBlock]:
        """Get all blocks for a specific node"""
        return [b for b in self.blocks if b.node_id == node_id]

    def get_agent_total_credit(self, agent_id: str) -> float:
        """Sum of all credits earned by an agent"""
        return sum(b.reward_credit for b in self.blocks if b.agent_id == agent_id)

    def get_agent_total_contributions(self, agent_id: str) -> int:
        """Count of contributions by an agent"""
        return len(self.get_blocks_by_agent(agent_id))

    def get_latest_blocks(self, limit: int = 20) -> list[LedgerBlock]:
        """Get the most recent blocks"""
        return self.blocks[-limit:]

    def verify_chain(self) -> bool:
        """Verify the hash chain integrity"""
        for i in range(1, len(self.blocks)):
            current = self.blocks[i]
            previous = self.blocks[i - 1]
            if current.previous_hash != previous.block_hash:
                logger.error(
                    f"[Ledger] Chain broken at block {i}: "
                    f"expected {previous.block_hash[:8]}..., "
                    f"got {current.previous_hash[:8]}..."
                )
                return False
        return True

    # ---- genesis block ----

    def create_genesis_block(self, founder_id: str) -> LedgerBlock:
        """
        Create the genesis (first) block of the Intelligence Ledger.

        This is NOT a super-admin privilege.
        It is a historical marker of AGT Network origin.
        No special permissions are derived from it.
        """
        if self.blocks:
            raise ValueError("Genesis block already exists")

        import uuid

        # Minimal genesis proof
        genesis_proof = IntelligenceProof(
            proof_id="poi-genesis-000000000000",
            task_id="genesis-000",
            task_name="AGT Network Genesis",
            agent_id=founder_id,
            node_id="genesis-node",
            contribution_type="knowledge_organization",
            difficulty=1,
            quality_score=100,
            verification_score=100,
            innovation_score=100,
            task_value=0,
            task_source="genesis",
            validator_node_id="genesis-node",
            validator_agent_id="genesis-core",
            validator_feedback="AGT Network Genesis — 第一个智能经济体实验协议诞生。",
        )

        block = LedgerBlock(
            block_id="blk-genesis-00000000",
            index=0,
            node_id="genesis-node",
            agent_id=founder_id,
            task_id="genesis-000",
            contribution_proof=genesis_proof,
            reputation_change=0,
            reward_credit=0,
            previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
        )

        block.block_hash = block.compute_hash()
        self.blocks.append(block)

        self.total_contributions = 1
        self.total_credit_issued = 0.0

        logger.info("[Ledger] Genesis block created — AGT Network origin recorded")
        self.save()
        return block
