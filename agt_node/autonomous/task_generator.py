"""
Autonomous Engine — Task Generator (v0.3)

Allows Agents to discover value opportunities and create task proposals
autonomously — without human intermediation.

Flow:
    Agent scans for opportunities
        ↓
    Creates Task Proposal
        ↓
    Stakes AGT Credit
        ↓
    Novelty Check (duplicate detection)
        ↓
    Listed in Task Pool (available for execution)
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .opportunity_detector import Opportunity, OpportunityType
from task_engine.tasks import AGTTask, TaskSource, TaskType

logger = logging.getLogger(__name__)


# Minimum reputation required to propose tasks
MIN_PROPOSER_REPUTATION = 150

# AGT Credit stake required per proposal
PROPOSAL_STAKE = 5.0

# Max proposals per agent per epoch
MAX_PROPOSALS_PER_EPOCH = 10


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    STAKED = "staked"
    LISTED = "listed"       # In task pool, available for claiming
    REJECTED = "rejected"   # Failed novelty check or insufficient stake
    COMPLETED = "completed" # Task was executed and validated


@dataclass
class TaskProposal:
    """A task proposal created by an Agent"""
    proposal_id: str
    proposer_agent_id: str
    proposer_node_id: str

    # Content
    title: str
    description: str
    goal: str
    task_type: str  # code_optimization, knowledge_organization, etc.

    # Economics
    proposed_value: float  # AGT Credit
    difficulty: int  # 1-10
    staked_amount: float = 0.0

    # Verification
    novelty_hash: str = ""
    status: ProposalStatus = ProposalStatus.DRAFT
    source: str = "agent_generated"

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    listed_task_id: str = ""  # Task ID after listing in pool

    def to_task_dict(self) -> dict:
        """Convert to AGTTask-compatible format for the task pool"""
        return {
            "id": self.proposal_id,
            "name": self.title,
            "description": self.description,
            "goal": self.goal,
            "source": self.source,
            "creator": self.proposer_agent_id,
            "type": self.task_type,
            "difficulty": self.difficulty,
            "value": self.proposed_value,
            "requirement": self.description,
            "validator_instructions": f"Validate that the output achieves: {self.goal}",
            "context": {"proposal_id": self.proposal_id, "staked": self.staked_amount},
            "status": "open",
        }

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "proposer_agent_id": self.proposer_agent_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "proposed_value": self.proposed_value,
            "difficulty": self.difficulty,
            "staked_amount": self.staked_amount,
            "status": self.status.value,
            "novelty_hash": self.novelty_hash,
        }


class TaskGenerator:
    """
    Autonomous Task Generator.

    Enables Agents to:
    1. Discover value opportunities (via OpportunityDetector)
    2. Create task proposals
    3. Stake AGT Credit (lost on spam rejection)
    4. Pass novelty check
    5. List tasks in the task pool
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._proposals: dict[str, TaskProposal] = {}
        self._novelty_hashes: set[str] = set()  # Recent proposal hashes
        self._agent_proposal_counts: dict[str, int] = {}  # agent_id → count this epoch

    def create_proposal(
        self,
        agent_id: str,
        title: str,
        description: str,
        goal: str,
        task_type: str,
        difficulty: int = 3,
        value: float = 20.0,
        reputation: float = 100.0,
    ) -> Optional[TaskProposal]:
        """
        Create a new task proposal from an Agent.

        Args:
            agent_id: The proposing agent
            title, description, goal: Task definition
            task_type: Type of task
            difficulty: 1-10
            value: Proposed AGT Credit value
            reputation: Agent's current reputation

        Returns:
            TaskProposal if successful, None if rejected
        """
        # Gate 1: Reputation check
        if reputation < MIN_PROPOSER_REPUTATION:
            logger.info(
                f"[TaskGen] Agent {agent_id} cannot propose: "
                f"reputation {reputation} < {MIN_PROPOSER_REPUTATION}"
            )
            return None

        # Gate 2: Rate limit
        count = self._agent_proposal_counts.get(agent_id, 0)
        if count >= MAX_PROPOSALS_PER_EPOCH:
            logger.info(f"[TaskGen] Agent {agent_id} rate limited ({count} proposals this epoch)")
            return None

        proposal_id = f"prop-{uuid.uuid4().hex[:8]}"

        # Compute novelty hash
        core = f"{task_type}:{title}:{goal}"
        novelty_hash = hashlib.sha256(core.encode()).hexdigest()

        # Gate 3: Novelty check (against all proposals, listed or not)
        for existing in self._proposals.values():
            if existing.novelty_hash == novelty_hash:
                logger.info(f"[TaskGen] Duplicate proposal detected: {title}")
                return None

        # Count this proposal toward rate limit
        self._agent_proposal_counts[agent_id] = count + 1

        proposal = TaskProposal(
            proposal_id=proposal_id,
            proposer_agent_id=agent_id,
            proposer_node_id=self.node_id,
            title=title,
            description=description,
            goal=goal,
            task_type=task_type,
            proposed_value=max(5.0, min(200.0, value)),
            difficulty=max(1, min(10, difficulty)),
            novelty_hash=novelty_hash,
            status=ProposalStatus.DRAFT,
        )

        self._proposals[proposal_id] = proposal
        logger.info(f"[TaskGen] Proposal {proposal_id} created by Agent {agent_id}: {title}")
        return proposal

    def stake_and_list(self, proposal_id: str, wallet_balance: float) -> bool:
        """
        Stake AGT Credit on a proposal and list it in the task pool.

        Args:
            proposal_id: The proposal to stake
            wallet_balance: Available balance (must cover stake)

        Returns:
            True if staked and listed, False otherwise
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return False

        if wallet_balance < PROPOSAL_STAKE:
            logger.info(f"[TaskGen] Insufficient stake for {proposal_id}")
            return False

        proposal.staked_amount = PROPOSAL_STAKE
        proposal.status = ProposalStatus.LISTED

        logger.info(
            f"[TaskGen] Proposal {proposal_id} staked ({PROPOSAL_STAKE} AGT) and LISTED"
        )
        return True

    def reject_proposal(self, proposal_id: str, reason: str = "") -> bool:
        """
        Reject a proposal (spam, duplicate, invalid).
        Stake is lost.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return False

        proposal.status = ProposalStatus.REJECTED
        logger.info(f"[TaskGen] Proposal {proposal_id} REJECTED: {reason}")
        return True

    def mark_completed(self, proposal_id: str, task_id: str):
        """Mark a proposal as completed (its task was executed and validated)"""
        proposal = self._proposals.get(proposal_id)
        if proposal:
            proposal.status = ProposalStatus.COMPLETED
            proposal.listed_task_id = task_id

    def get_listed_proposals(self) -> list[TaskProposal]:
        """Get all proposals ready for the task pool"""
        return [p for p in self._proposals.values() if p.status == ProposalStatus.LISTED]

    def get_proposal(self, proposal_id: str) -> Optional[TaskProposal]:
        return self._proposals.get(proposal_id)

    def reset_epoch_counters(self):
        """Reset per-epoch proposal counts"""
        self._agent_proposal_counts.clear()
        logger.info("[TaskGen] Epoch proposal counters reset")

    def stats(self) -> dict:
        return {
            "total_proposals": len(self._proposals),
            "listed": len(self.get_listed_proposals()),
            "by_status": {
                status.value: sum(1 for p in self._proposals.values() if p.status == status)
                for status in ProposalStatus
            },
            "proposers_this_epoch": len(self._agent_proposal_counts),
        }
