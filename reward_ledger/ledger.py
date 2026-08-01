"""
Intelligence Ledger — 智能贡献账本

Records the history of Agent intelligence contributions.
This is NOT a cryptocurrency ledger — it tracks intellectual value creation.
Future: AGT Token will be a mapping over this ledger.

v0.1.1: Full block persistence + supply guard.
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

# Default max supply (matches emission.py: EmissionConfig.max_supply)
DEFAULT_MAX_SUPPLY = 1_000_000_000.0  # 1 billion


@dataclass
class LedgerBlock:
    """
    A single block in the Intelligence Ledger.

    Each block records one verified intelligence contribution.
    Blocks are chained via previous_hash for tamper evidence.

    Immutability: block_hash can only be set once (on creation).
    Attempting to modify it after creation raises ValueError.
    """

    block_id: str
    index: int
    node_id: str
    agent_id: str
    task_id: str

    # Core payload
    contribution_proof: IntelligenceProof
    reputation_change: float = 0.0
    reward_credit: float = 0.0

    # Chain integrity
    previous_hash: str = ""
    block_hash: str = ""

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Immutability guard
    _sealed: bool = field(default=False, repr=False)

    def __post_init__(self):
        """After creation, seal the block to prevent hash modification"""
        # Only seal if block_hash was explicitly set by creator
        if self.block_hash:
            self._sealed = True

    def seal(self):
        """Compute and lock the block hash — irreversible"""
        if self._sealed:
            raise ValueError(f"Block {self.block_id} is already sealed")
        self.block_hash = self.compute_hash()
        self._sealed = True

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

    @classmethod
    def from_dict(cls, data: dict) -> "LedgerBlock":
        """Restore a LedgerBlock from its dict representation"""
        proof = None
        if data.get("proof"):
            proof = IntelligenceProof.from_dict(data["proof"])

        block = cls(
            block_id=data["block_id"],
            index=data["index"],
            node_id=data["node_id"],
            agent_id=data["agent_id"],
            task_id=data["task_id"],
            contribution_proof=proof,
            reputation_change=data.get("reputation_change", 0.0),
            reward_credit=data.get("reward_credit", 0.0),
            previous_hash=data.get("previous_hash", ""),
            block_hash=data.get("block_hash", ""),
            timestamp=data.get("timestamp", ""),
        )
        # Restore sealed state
        if block.block_hash:
            block._sealed = True
        return block


class IntelligenceLedger:
    """
    Intelligence Ledger — the core ledger of the AGT Network.

    v0.1.1: Full persistence.
    - Every block is appended to ledger_blocks.jsonl immediately.
    - On restart, load() restores the full chain and verifies integrity.
    - Supply guard prevents infinite credit issuance.

    Key distinction:
        NOT a wallet: doesn't track balances.
        IS a history: each block records value creation.
    """

    def __init__(self, data_dir: str = "./data", max_supply: float = DEFAULT_MAX_SUPPLY):
        self.data_dir = data_dir
        self.blocks: list[LedgerBlock] = []
        self.max_supply = max_supply

        # File paths
        self._blocks_path = os.path.join(data_dir, "ledger_blocks.jsonl")
        self._meta_path = os.path.join(data_dir, "intelligence_ledger.json")

        # Stats (derived from blocks)
        self.total_credit_issued: float = 0.0
        self.total_contributions: int = 0

    # ============================================================
    # Persistence
    # ============================================================

    def load(self) -> bool:
        """
        Load the full ledger from disk.

        Reads ledger_blocks.jsonl line-by-line, restores every block,
        verifies the hash chain, and rebuilds stats.

        Returns True if chain integrity is verified, False if broken.
        """
        os.makedirs(self.data_dir, exist_ok=True)

        if not os.path.exists(self._blocks_path):
            logger.info("[Ledger] No persisted blocks found — fresh ledger")
            return True

        self.blocks = []
        load_errors = 0

        try:
            with open(self._blocks_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        block = LedgerBlock.from_dict(data)
                        self.blocks.append(block)
                    except Exception as e:
                        load_errors += 1
                        logger.warning(f"[Ledger] Block at line {line_num} failed to parse: {e}")
        except Exception as e:
            logger.error(f"[Ledger] Failed to read blocks file: {e}")
            return False

        if load_errors:
            logger.warning(f"[Ledger] {load_errors} blocks failed to load")

        # Rebuild stats from loaded blocks
        self.total_contributions = len(self.blocks)
        self.total_credit_issued = sum(b.reward_credit for b in self.blocks)

        logger.info(
            f"[Ledger] Loaded {len(self.blocks)} blocks, "
            f"{self.total_credit_issued:.1f} AGT Credit issued"
        )

        # Verify chain integrity
        if not self.verify_chain():
            logger.error(
                "[Ledger] CHAIN INTEGRITY BROKEN! "
                "The ledger may have been tampered with."
            )
            return False

        logger.info("[Ledger] Chain integrity VERIFIED")
        return True

    def _persist_block(self, block: LedgerBlock):
        """Append a single block to the JSONL file (atomic append)"""
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            block_json = json.dumps(block.to_dict(), ensure_ascii=False)
            with open(self._blocks_path, "a", encoding="utf-8") as f:
                f.write(block_json + "\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            logger.error(f"[Ledger] Failed to persist block {block.block_id}: {e}")
            raise

    def _save_metadata(self):
        """Persist ledger metadata (non-critical, for quick stat access)"""
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            metadata = {
                "total_credit_issued": self.total_credit_issued,
                "total_contributions": self.total_contributions,
                "last_block_hash": self.blocks[-1].block_hash if self.blocks else "",
                "block_count": len(self.blocks),
            }
            with open(self._meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[Ledger] Metadata save failed: {e}")

    # ============================================================
    # Supply Guard
    # ============================================================

    def _check_supply(self, reward_credit: float):
        """
        Verify that issuing this reward won't exceed max_supply.

        Raises ValueError if the supply limit would be exceeded.
        """
        if self.total_credit_issued + reward_credit > self.max_supply:
            raise ValueError(
                f"Supply guard: cannot issue {reward_credit:.1f} AGT Credit. "
                f"Issued: {self.total_credit_issued:.1f}, "
                f"Max: {self.max_supply:.1f}, "
                f"Overflow: {(self.total_credit_issued + reward_credit - self.max_supply):.1f}"
            )

    def supply_remaining(self) -> float:
        """Remaining AGT Credit that can still be issued"""
        return max(0.0, self.max_supply - self.total_credit_issued)

    def supply_used_pct(self) -> float:
        """Percentage of max supply already issued"""
        if self.max_supply == 0:
            return 100.0
        return (self.total_credit_issued / self.max_supply) * 100.0

    # ============================================================
    # Block Creation
    # ============================================================

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
        Intelligence Proof into a permanent, immutable record.

        Enforces supply guard: raises ValueError if max_supply exceeded.
        """
        import uuid

        # P0-2: Supply guard
        self._check_supply(reward_credit)

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

        # Seal: compute hash and lock (immutable)
        block.seal()

        # Persist to disk immediately (P0-1)
        self._persist_block(block)

        # Update in-memory state
        self.blocks.append(block)
        self.total_contributions += 1
        self.total_credit_issued += reward_credit

        logger.info(
            f"[Ledger] Block {block.index} created: "
            f"Agent={agent_id}, "
            f"Reward={reward_credit:.1f} AGT Credit, "
            f"Rep Δ={reputation_change:+.1f}, "
            f"Supply: {self.supply_used_pct():.4f}%"
        )

        self._save_metadata()
        return block

    # ============================================================
    # Queries
    # ============================================================

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
        """Verify the hash chain integrity across all blocks"""
        for i in range(1, len(self.blocks)):
            current = self.blocks[i]
            previous = self.blocks[i - 1]
            if current.previous_hash != previous.block_hash:
                logger.error(
                    f"[Ledger] Chain BROKEN at block {i}: "
                    f"expected {previous.block_hash[:16]}..., "
                    f"got {current.previous_hash[:16]}..."
                )
                return False
            # Also verify each block's own hash
            if current.block_hash != current.compute_hash():
                logger.error(
                    f"[Ledger] Block {i} hash MISMATCH: "
                    f"stored={current.block_hash[:16]}..., "
                    f"computed={current.compute_hash()[:16]}..."
                )
                return False
        return True

    # ============================================================
    # Genesis Block
    # ============================================================

    def create_genesis_block(self, founder_id: str) -> LedgerBlock:
        """
        Create the genesis (first) block of the Intelligence Ledger.

        This is NOT a super-admin privilege.
        It is a historical marker of AGT Network origin.
        No special permissions are derived from it.
        """
        if self.blocks:
            raise ValueError("Genesis block already exists")

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

        block.seal()

        # Persist genesis block (P0-1)
        os.makedirs(self.data_dir, exist_ok=True)

        # If loading from existing file, don't overwrite
        if os.path.exists(self._blocks_path) and os.path.getsize(self._blocks_path) > 0:
            logger.info("[Ledger] Blocks file exists — genesis already persisted")
        else:
            # Clear/create the blocks file and write genesis
            self._persist_block(block)

        self.blocks.append(block)
        self.total_contributions = 1
        self.total_credit_issued = 0.0

        logger.info("[Ledger] Genesis block created — AGT Network origin recorded")
        self._save_metadata()
        return block
