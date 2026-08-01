"""
Agent Marketplace — v0.3 Autonomous Economy

Matches task proposals with qualified executors.
NOT a bidding system. NOT a token exchange.
A discovery and claiming mechanism for the Agent labor market.

Features:
- Task pool: all open tasks visible to qualified agents
- Claiming (not bidding): first qualified agent claims
- Capability matching: agents see only tasks they're qualified for
- Qualification check: reputation + capability + validator distance
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Default claim TTL in seconds
CLAIM_TTL = 300  # 5 minutes


@dataclass
class ClaimRecord:
    """A claim by an agent on a task"""
    claim_id: str
    task_id: str
    agent_id: str
    node_id: str
    claimed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = ""
    status: str = "active"  # active | executed | expired


class AgentMarketplace:
    """
    Agent Marketplace — intelligent labor matching.

    Responsibilities:
    1. Maintain the task pool (open tasks)
    2. Match qualified agents to tasks
    3. Handle claiming (one task → one executor)
    4. Track claim lifecycle
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._task_pool: dict[str, dict] = {}  # task_id → task_dict
        self._claims: dict[str, ClaimRecord] = {}  # claim_id → record
        self._agent_claims: dict[str, list[str]] = {}  # agent_id → [claim_ids]

    # ---- Task Pool ----

    def list_task(self, task: dict):
        """Add a task to the marketplace pool"""
        self._task_pool[task["id"]] = task
        logger.info(f"[Marketplace] Task listed: {task['id']} ({task.get('name', '')})")

    def list_tasks(self, tasks: list[dict]):
        """Add multiple tasks"""
        for t in tasks:
            self.list_task(t)

    def remove_task(self, task_id: str):
        """Remove a task from the pool"""
        self._task_pool.pop(task_id, None)

    def get_open_tasks(
        self,
        agent_reputation: float = 0,
        agent_capability_stars: dict[str, int] = None,
        agent_node_id: str = "",
    ) -> list[dict]:
        """
        Get tasks that an agent is qualified to execute.

        Filters:
        - Reputation meets minimum
        - Capability matches task domain
        - Agent is not the proposer (for agent_generated tasks)
        - Validator distance: high-difficulty tasks need different nodes
        """
        qualified = []
        capability_stars = agent_capability_stars or {}

        for task_id, task in self._task_pool.items():
            if task.get("status") != "open":
                continue

            difficulty = task.get("difficulty", 1)

            # Reputation gate
            min_rep = self._min_reputation_for_difficulty(difficulty)
            if agent_reputation < min_rep:
                continue

            # Capability gate
            task_type = task.get("type", "")
            domain = self._task_type_to_domain(task_type)
            required_stars = self._min_stars_for_difficulty(difficulty)
            agent_stars = capability_stars.get(domain, 1)
            if agent_stars < required_stars:
                continue

            # Proposer gate: agent cannot execute their own proposal
            if task.get("source") == "agent_generated" and task.get("creator") == agent_reputation:
                continue

            # Validator distance gate (high-difficulty tasks)
            if difficulty >= 7:
                task_creator_node = task.get("context", {}).get("proposer_node_id", "")
                if task_creator_node == agent_node_id:
                    continue

            qualified.append(task)

        return qualified

    # ---- Claiming ----

    def claim_task(
        self,
        task_id: str,
        agent_id: str,
        node_id: str,
    ) -> Optional[ClaimRecord]:
        """
        Claim a task for execution.

        First qualified agent to claim gets the task.
        Claim has a TTL — if not executed within TTL, the task re-opens.
        """
        import uuid

        task = self._task_pool.get(task_id)
        if not task or task.get("status") != "open":
            return None

        # Mark task as claimed
        task["status"] = "claimed"
        task["claimed_by"] = agent_id

        claim = ClaimRecord(
            claim_id=f"claim-{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            agent_id=agent_id,
            node_id=node_id,
        )

        self._claims[claim.claim_id] = claim
        if agent_id not in self._agent_claims:
            self._agent_claims[agent_id] = []
        self._agent_claims[agent_id].append(claim.claim_id)

        logger.info(f"[Marketplace] Task {task_id} claimed by Agent {agent_id}")
        return claim

    def release_claim(self, claim_id: str):
        """Release a claim (task re-opens)"""
        claim = self._claims.get(claim_id)
        if not claim:
            return

        task = self._task_pool.get(claim.task_id)
        if task:
            task["status"] = "open"
            task.pop("claimed_by", None)

        claim.status = "expired"
        logger.info(f"[Marketplace] Claim {claim_id} released — task {claim.task_id} re-opened")

    def mark_executed(self, claim_id: str, proof_id: str):
        """Mark a claimed task as executed"""
        claim = self._claims.get(claim_id)
        if claim:
            claim.status = "executed"

        # Remove task from pool
        if claim:
            self._task_pool.pop(claim.task_id, None)

    def get_agent_claims(self, agent_id: str) -> list[ClaimRecord]:
        """Get all claims by an agent"""
        claim_ids = self._agent_claims.get(agent_id, [])
        return [self._claims[cid] for cid in claim_ids if cid in self._claims]

    # ---- Lookup tables ----

    @staticmethod
    def _min_reputation_for_difficulty(difficulty: int) -> float:
        if difficulty <= 3: return 0
        if difficulty <= 6: return 10
        if difficulty <= 8: return 30
        return 50

    @staticmethod
    def _min_stars_for_difficulty(difficulty: int) -> int:
        if difficulty <= 3: return 1
        if difficulty <= 6: return 2
        if difficulty <= 8: return 3
        return 4

    @staticmethod
    def _task_type_to_domain(task_type: str) -> str:
        mapping = {
            "code_optimization": "python",
            "code_creation": "python",
            "knowledge_organization": "research",
            "agent_capability_test": "creative_design",
            "tool_development": "python",
            "analysis": "data_analysis",
            "research": "research",
            "creative_design": "creative_design",
        }
        return mapping.get(task_type, "research")

    # ----

    def stats(self) -> dict:
        open_count = sum(1 for t in self._task_pool.values() if t.get("status") == "open")
        claimed_count = sum(1 for t in self._task_pool.values() if t.get("status") == "claimed")
        return {
            "tasks_in_pool": len(self._task_pool),
            "open": open_count,
            "claimed": claimed_count,
            "active_claims": sum(1 for c in self._claims.values() if c.status == "active"),
        }
