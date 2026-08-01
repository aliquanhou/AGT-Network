"""
Task Engine — Dispatcher

Handles task distribution among agents in the network.
Ensures validator != worker (no self-validation).
"""

import logging
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .tasks import AGTTask

logger = logging.getLogger(__name__)


@dataclass
class TaskAssignment:
    """Record of a task assigned to an agent"""
    assignment_id: str
    task: AGTTask
    worker_node_id: str
    worker_agent_id: str
    validator_node_id: str
    validator_agent_id: str
    assigned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "assigned"  # assigned | submitted | validated | rewarded


class TaskDispatcher:
    """
    Task dispatcher.

    Rules:
    1. A task is assigned to a worker agent and a validator agent.
    2. The worker and validator MUST be from different nodes.
    3. v0.1: Round-robin assignment among known nodes.
    """

    def __init__(self):
        self.assignments: dict[str, TaskAssignment] = {}
        self._pending_tasks: list[AGTTask] = []

    # ---- task pool management ----

    def add_task(self, task: AGTTask):
        """Add a task to the dispatch pool (deep-copied to preserve original)"""
        self._pending_tasks.append(deepcopy(task))
        logger.info(f"[Dispatcher] Task added to pool: {task.id} ({task.name})")

    def add_tasks(self, tasks: list[AGTTask]):
        """Add multiple tasks"""
        for t in tasks:
            self.add_task(t)

    def get_pending_tasks(self) -> list[AGTTask]:
        """Get all unassigned tasks"""
        return self._pending_tasks

    def get_open_tasks(self) -> list[dict]:
        """Get open tasks as dicts (for API display)"""
        return [t.to_dict() for t in self._pending_tasks if t.status == "open"]

    # ---- assignment logic ----

    def assign_task(
        self,
        task_id: str,
        worker_node_id: str,
        worker_agent_id: str,
        validator_node_id: str,
        validator_agent_id: str,
    ) -> Optional[TaskAssignment]:
        """
        Assign a task to a worker and a validator.

        CRITICAL: worker_node_id != validator_node_id
        """
        if worker_node_id == validator_node_id:
            logger.error(
                f"[Dispatcher] Cannot assign: worker and validator "
                f"are on the same node ({worker_node_id}). Rejected."
            )
            return None

        # Find the task
        task = None
        for i, t in enumerate(self._pending_tasks):
            if t.id == task_id and t.status == "open":
                task = t
                self._pending_tasks.pop(i)
                break

        if task is None:
            logger.warning(f"[Dispatcher] Task {task_id} not found or not open")
            return None

        task.status = "claimed"

        assignment = TaskAssignment(
            assignment_id=str(uuid.uuid4()),
            task=task,
            worker_node_id=worker_node_id,
            worker_agent_id=worker_agent_id,
            validator_node_id=validator_node_id,
            validator_agent_id=validator_agent_id,
        )

        self.assignments[assignment.assignment_id] = assignment
        logger.info(
            f"[Dispatcher] Task {task_id} assigned: "
            f"Worker={worker_node_id}/{worker_agent_id}, "
            f"Validator={validator_node_id}/{validator_agent_id}"
        )

        return assignment

    def auto_assign(
        self,
        task_id: str,
        available_nodes: list[dict],
    ) -> Optional[TaskAssignment]:
        """
        Auto-assign a task: pick first available node as worker,
        and a different node as validator.

        Args:
            task_id: Task to assign
            available_nodes: List of {"node_id": ..., "agent_ids": [...]}

        Returns:
            TaskAssignment or None if insufficient nodes
        """
        if len(available_nodes) < 2:
            logger.warning(
                "[Dispatcher] Need at least 2 nodes for auto-assign "
                "(worker + validator from different nodes)"
            )
            return None

        # Worker: first node's first agent
        worker_node = available_nodes[0]
        worker_agent = worker_node["agent_ids"][0] if worker_node["agent_ids"] else "default-agent"

        # Validator: second node's first agent
        validator_node = available_nodes[1]
        validator_agent = validator_node["agent_ids"][0] if validator_node["agent_ids"] else "default-agent"

        return self.assign_task(
            task_id=task_id,
            worker_node_id=worker_node["node_id"],
            worker_agent_id=worker_agent,
            validator_node_id=validator_node["node_id"],
            validator_agent_id=validator_agent,
        )

    # ---- status updates ----

    def mark_submitted(self, assignment_id: str):
        """Mark a task assignment as submitted"""
        if assignment_id in self.assignments:
            self.assignments[assignment_id].status = "submitted"
            self.assignments[assignment_id].task.status = "completed"

    def mark_validated(self, assignment_id: str):
        """Mark as validated"""
        if assignment_id in self.assignments:
            self.assignments[assignment_id].status = "validated"
            self.assignments[assignment_id].task.status = "validated"

    def mark_rewarded(self, assignment_id: str):
        """Mark as rewarded"""
        if assignment_id in self.assignments:
            self.assignments[assignment_id].status = "rewarded"
            self.assignments[assignment_id].task.status = "rewarded"

    # ---- query ----

    def get_assignment(self, assignment_id: str) -> Optional[TaskAssignment]:
        return self.assignments.get(assignment_id)
