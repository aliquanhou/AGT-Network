"""
Agent Runtime — Agent Main Class

AGT Agent = Planner + Executor + Tools + Memory

An Agent receives a task, plans its execution,
executes the steps, and returns the result.

Usage:
    agent = AGTAgent(agent_id="agent-001", llm_client=llm)
    result = await agent.run_task(task)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .llm_client import LLMClient
from .planner import Planner, Plan
from .executor import Executor, ExecutionResult
from .tools import build_tool_registry

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A memory record stored by the agent"""
    timestamp: str
    type: str  # "task", "observation", "error"
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskResult:
    """Complete task execution result from an agent"""
    agent_id: str
    task_id: str
    plan: Plan
    execution: ExecutionResult
    started_at: str
    completed_at: str
    duration_seconds: float
    llm_usage: dict = field(default_factory=dict)  # v0.36.4: {tokens, cost}


class AGTAgent:
    """
    AGT Agent — the intelligent worker node.

    Capabilities:
    - Receives tasks (goals)
    - Plans execution (Planner)
    - Executes steps (Executor)
    - Uses tools (Tool registry)
    - Maintains memory (Memory)

    Architecture:
        Agent
         ├── Planner   → Plan
         ├── Executor  → StepResult[]
         ├── Tool[]    → built-in tools
         └── Memory    → MemoryEntry[]
    """

    def __init__(
        self,
        agent_id: str,
        llm_client: LLMClient,
        name: str = "",
        owner_node_id: str = "",
    ):
        self.agent_id = agent_id
        self.name = name or agent_id
        self.owner_node_id = owner_node_id

        # Core components
        self.llm = llm_client
        self.planner = Planner(self.llm)
        self.executor = Executor(self.llm)
        self.tools = build_tool_registry()

        # Memory
        self.memory: list[MemoryEntry] = []

        # Stats
        self.tasks_completed: int = 0
        self.total_reward: float = 0.0

    async def run_task(self, task: dict) -> TaskResult:
        """
        Run a complete task lifecycle.

        Args:
            task: Task dict with "id", "goal", "difficulty", etc.

        Returns:
            TaskResult with plan, execution, and timing info.
        """
        task_id = task.get("id", "unknown")
        goal = task.get("goal", task.get("name", "Unnamed task"))
        context = task.get("context", {})

        started_at = datetime.now().isoformat()
        t0 = datetime.now()

        logger.info(f"[Agent:{self.agent_id}] Running task {task_id}: {goal}")

        # 1. Plan
        plan = await self.planner.plan(goal, context)

        # 2. Execute
        execution = await self.executor.execute(plan)

        t1 = datetime.now()
        duration = (t1 - t0).total_seconds()
        completed_at = t1.isoformat()

        # 2.5 Capture LLM usage (v0.36.4)
        llm_usage = {}
        if self.llm:
            llm_usage = {
                "total_tokens": getattr(self.llm, "total_tokens", 0),
                "total_cost": round(getattr(self.llm, "total_cost", 0.0), 6),
                "provider": getattr(self.llm, "model", "unknown"),
            }

        # 3. Record in memory
        self._remember(
            "task",
            f"Completed task {task_id}: {goal}",
            {"task_id": task_id, "success": execution.success, "duration": duration},
        )

        self.tasks_completed += 1

        return TaskResult(
            agent_id=self.agent_id,
            task_id=task_id,
            plan=plan,
            execution=execution,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            llm_usage=llm_usage,
        )

    def add_reward(self, amount: float):
        """Record earned reward"""
        self.total_reward += amount
        self._remember(
            "observation",
            f"Received reward: {amount} AGT",
            {"reward": amount, "total": self.total_reward},
        )

    # ---- Memory ----

    def _remember(self, entry_type: str, content: str, metadata: dict = None):
        """Store a memory entry"""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            type=entry_type,
            content=content,
            metadata=metadata or {},
        )
        self.memory.append(entry)

        # Keep memory bounded (v0.1: last 1000 entries)
        if len(self.memory) > 1000:
            self.memory = self.memory[-1000:]

    def recall(self, entry_type: str = None, limit: int = 10) -> list[MemoryEntry]:
        """Recall memory entries by type"""
        entries = self.memory
        if entry_type:
            entries = [e for e in entries if e.type == entry_type]
        return entries[-limit:]

    # ---- Info ----

    def status(self) -> dict:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "owner_node_id": self.owner_node_id,
            "tasks_completed": self.tasks_completed,
            "total_reward": self.total_reward,
            "memory_size": len(self.memory),
            "tools": list(self.tools.keys()),
        }
