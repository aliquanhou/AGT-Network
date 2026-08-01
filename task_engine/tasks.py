"""
Task Engine — Genesis Task Definitions

AGT Network v0.1: Hardcoded Genesis tasks.
Task sources: genesis / agent_generated / human_request / enterprise.

Genesis Mission: "Build the AGT AI Knowledge Civilization"
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskSource(str, Enum):
    GENESIS = "genesis"
    AGENT_GENERATED = "agent_generated"
    HUMAN_REQUEST = "human_request"
    ENTERPRISE = "enterprise"


class TaskType(str, Enum):
    CODE_OPTIMIZATION = "code_optimization"
    KNOWLEDGE_ORGANIZATION = "knowledge_organization"
    AGENT_CAPABILITY_TEST = "agent_capability_test"
    TOOL_DEVELOPMENT = "tool_development"


@dataclass
class AGTTask:
    """
    AGT Task definition.

    Contains all metadata for task lifecycle:
    creation → dispatch → execution → validation → reward.
    """
    id: str
    name: str
    description: str
    goal: str

    # Classification
    source: TaskSource = TaskSource.GENESIS
    creator: str = "AGT_CORE"
    task_type: TaskType = TaskType.CODE_OPTIMIZATION
    difficulty: int = 1  # 1–10
    value: float = 10.0  # Base value in AGT Credits

    # Execution
    requirement: str = ""  # Human-readable requirement
    validator_instructions: str = ""  # Instructions for the Validator Agent
    context: dict = field(default_factory=dict)

    # State
    status: str = "open"  # open | claimed | completed | validated | rewarded

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goal": self.goal,
            "source": self.source.value,
            "creator": self.creator,
            "type": self.task_type.value,
            "difficulty": self.difficulty,
            "value": self.value,
            "requirement": self.requirement,
            "validator_instructions": self.validator_instructions,
            "context": self.context,
            "status": self.status,
        }


# ============================================================
# Genesis Missions — Initial Tasks
# ============================================================

GENESIS_TASKS: list[AGTTask] = [
    AGTTask(
        id="genesis-001",
        name="Code Optimization: Sort Algorithm",
        description=(
            "Analyze a given sorting algorithm implementation and "
            "propose optimizations with benchmarks."
        ),
        goal=(
            "Review a bubble sort implementation, identify performance issues, "
            "and provide an optimized version with complexity analysis."
        ),
        source=TaskSource.GENESIS,
        creator="AGT_CORE",
        task_type=TaskType.CODE_OPTIMIZATION,
        difficulty=3,
        value=30.0,
        requirement=(
            "Output must include: (1) identified issues, "
            "(2) optimized code, (3) complexity comparison, "
            "(4) benchmark recommendations."
        ),
        validator_instructions=(
            "Check: Did the agent correctly identify O(n²) complexity of bubble sort? "
            "Did they propose a valid alternative (e.g., quicksort, mergesort)? "
            "Is the optimized code syntactically correct? "
            "Are the complexity claims accurate? "
            "Score from 0–100 based on completeness and correctness."
        ),
        context={
            "sample_code": (
                "def bubble_sort(arr):\n"
                "    n = len(arr)\n"
                "    for i in range(n):\n"
                "        for j in range(0, n-i-1):\n"
                "            if arr[j] > arr[j+1]:\n"
                "                arr[j], arr[j+1] = arr[j+1], arr[j]\n"
                "    return arr"
            ),
            "language": "python",
        },
    ),

    AGTTask(
        id="genesis-002",
        name="Knowledge Organization: AGT Protocol Concepts",
        description=(
            "Research and organize key concepts related to Agent Economy Protocols "
            "and Proof of Intelligence into a structured knowledge entry."
        ),
        goal=(
            "Create a structured knowledge document covering: "
            "(1) What is an Agent Economy Protocol? "
            "(2) What is Proof of Intelligence? "
            "(3) How does it differ from Proof of Work and Proof of Stake? "
            "(4) Key use cases and applications."
        ),
        source=TaskSource.GENESIS,
        creator="AGT_CORE",
        task_type=TaskType.KNOWLEDGE_ORGANIZATION,
        difficulty=4,
        value=40.0,
        requirement=(
            "Output must be in markdown format, structured with headings, "
            "at least 4 sections, clear definitions, and practical examples."
        ),
        validator_instructions=(
            "Check: Are the concepts accurately defined? "
            "Is the comparison with PoW/PoS clear and correct? "
            "Is the document well-structured with proper markdown? "
            "Are there at least 4 sections? "
            "Is the analysis original (not obviously copy-pasted)? "
            "Score from 0–100 on accuracy, structure, and originality."
        ),
    ),

    AGTTask(
        id="genesis-003",
        name="Agent Capability Test: Creative Problem Solving",
        description=(
            "Test the agent's ability to solve a novel problem by "
            "designing a solution to a given challenge."
        ),
        goal=(
            "Design a decentralized task allocation system for AI agents. "
            "Consider: how tasks are matched to agents, how quality is ensured, "
            "how conflicts are resolved, and how rewards are distributed. "
            "Output a design document."
        ),
        source=TaskSource.GENESIS,
        creator="AGT_CORE",
        task_type=TaskType.AGENT_CAPABILITY_TEST,
        difficulty=7,
        value=70.0,
        requirement=(
            "Output must include: (1) system architecture overview, "
            "(2) task-agent matching algorithm description, "
            "(3) quality assurance mechanism, "
            "(4) conflict resolution approach, "
            "(5) reward distribution logic."
        ),
        validator_instructions=(
            "Check: Is the design coherent and internally consistent? "
            "Is the task-agent matching algorithm reasonably described? "
            "Does the quality assurance mechanism make sense? "
            "Is the reward distribution fair and logical? "
            "Does the solution address all 5 required aspects? "
            "Score from 0–100 based on completeness, coherence, and creativity."
        ),
    ),

    AGTTask(
        id="genesis-004",
        name="Tool Development: Text Summarizer Function",
        description=(
            "Develop a Python utility function that summarizes long texts "
            "using extractive or abstractive methods."
        ),
        goal=(
            "Design and implement a Python function `summarize(text, max_sentences=3)` "
            "that produces a concise summary of the input text. "
            "Include docstring, type hints, and example usage."
        ),
        source=TaskSource.GENESIS,
        creator="AGT_CORE",
        task_type=TaskType.TOOL_DEVELOPMENT,
        difficulty=5,
        value=50.0,
        requirement=(
            "Output must include: (1) the function implementation, "
            "(2) docstring and type hints, (3) example usage, "
            "(4) explanation of the summarization approach."
        ),
        validator_instructions=(
            "Check: Is the function syntactically correct Python? "
            "Does it have proper type hints and docstring? "
            "Does the summarization approach make sense? "
            "Are there example usages? "
            "Is the code clean and well-structured? "
            "Score from 0–100 on correctness, completeness, and code quality."
        ),
    ),
]


# ============================================================
# Factory
# ============================================================

def get_genesis_tasks() -> list[AGTTask]:
    """Return all Genesis tasks"""
    return GENESIS_TASKS


def get_task_by_id(task_id: str) -> Optional[AGTTask]:
    """Find a task by ID"""
    for t in GENESIS_TASKS:
        if t.id == task_id:
            return t
    return None
