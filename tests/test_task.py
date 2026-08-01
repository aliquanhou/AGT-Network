"""
Tests: Task Engine — Genesis Tasks + Dispatcher + Validator

Verifies:
- Genesis task definitions (source/creator/type/value fields)
- Task dispatch (worker != validator rule)
- Validator scoring (heuristic + self-validation block)
"""

import pytest

from task_engine.tasks import (
    AGTTask,
    TaskSource,
    TaskType,
    GENESIS_TASKS,
    get_genesis_tasks,
    get_task_by_id,
)
from task_engine.dispatcher import TaskDispatcher, TaskAssignment
from task_engine.validator import Validator, ValidationResult


# ============================================================
# Task Definition Tests
# ============================================================

class TestTaskDefinitions:
    def test_genesis_tasks_count(self):
        """4 Genesis tasks defined"""
        tasks = get_genesis_tasks()
        assert len(tasks) == 4

    def test_task_source_field(self):
        """Every task has source field"""
        for task in GENESIS_TASKS:
            assert task.source == TaskSource.GENESIS
            assert task.creator == "AGT_CORE"

    def test_task_type_field(self):
        """4 task types across Genesis tasks"""
        types = {t.task_type for t in GENESIS_TASKS}
        assert TaskType.CODE_OPTIMIZATION in types
        assert TaskType.KNOWLEDGE_ORGANIZATION in types
        assert TaskType.AGENT_CAPABILITY_TEST in types
        assert TaskType.TOOL_DEVELOPMENT in types

    def test_task_value_field(self):
        """Value scales with difficulty"""
        for task in GENESIS_TASKS:
            assert task.value >= 10.0
            assert task.difficulty >= 1
            assert task.difficulty <= 10

    def test_task_to_dict(self):
        task = GENESIS_TASKS[0]
        d = task.to_dict()
        assert d["source"] == "genesis"
        assert d["creator"] == "AGT_CORE"
        assert "type" in d
        assert "value" in d

    def test_get_task_by_id(self):
        task = get_task_by_id("genesis-001")
        assert task is not None
        assert task.name == "Code Optimization: Sort Algorithm"

    def test_get_task_by_id_not_found(self):
        assert get_task_by_id("nonexistent") is None


# ============================================================
# Dispatcher Tests
# ============================================================

class TestDispatcher:
    def test_add_task(self):
        dispatcher = TaskDispatcher()
        task = GENESIS_TASKS[0]
        dispatcher.add_task(task)
        assert len(dispatcher.get_pending_tasks()) == 1

    def test_add_multiple_tasks(self):
        dispatcher = TaskDispatcher()
        dispatcher.add_tasks(GENESIS_TASKS)
        assert len(dispatcher.get_pending_tasks()) == 4

    def test_assign_task_different_nodes(self):
        """Task assigned to different nodes for worker and validator"""
        dispatcher = TaskDispatcher()
        dispatcher.add_task(GENESIS_TASKS[0])

        assignment = dispatcher.assign_task(
            task_id="genesis-001",
            worker_node_id="node-a",
            worker_agent_id="agent-a1",
            validator_node_id="node-b",
            validator_agent_id="agent-b1",
        )
        assert assignment is not None
        assert assignment.worker_node_id == "node-a"
        assert assignment.validator_node_id == "node-b"
        assert assignment.worker_node_id != assignment.validator_node_id

    def test_assign_task_same_node_rejected(self):
        """SAME-NODE ASSIGNMENT BLOCKED — core rule"""
        dispatcher = TaskDispatcher()
        dispatcher.add_task(GENESIS_TASKS[0])

        assignment = dispatcher.assign_task(
            task_id="genesis-001",
            worker_node_id="node-a",
            worker_agent_id="agent-a1",
            validator_node_id="node-a",  # SAME NODE — VIOLATION
            validator_agent_id="agent-a2",
        )
        assert assignment is None  # Rejected!

    def test_auto_assign_needs_2_nodes(self):
        """Auto-assign requires at least 2 nodes"""
        dispatcher = TaskDispatcher()
        dispatcher.add_task(GENESIS_TASKS[0])

        # Only 1 node — should fail
        assignment = dispatcher.auto_assign("genesis-001", [
            {"node_id": "node-a", "agent_ids": ["agent-a1"]},
        ])
        assert assignment is None

    def test_auto_assign_success(self):
        """Auto-assign with 2+ nodes"""
        dispatcher = TaskDispatcher()
        dispatcher.add_task(GENESIS_TASKS[0])

        assignment = dispatcher.auto_assign("genesis-001", [
            {"node_id": "node-a", "agent_ids": ["agent-a1"]},
            {"node_id": "node-b", "agent_ids": ["agent-b1"]},
        ])
        assert assignment is not None
        assert assignment.worker_node_id == "node-a"
        assert assignment.validator_node_id == "node-b"

    def test_get_open_tasks(self):
        dispatcher = TaskDispatcher()
        dispatcher.add_tasks(GENESIS_TASKS)
        open_tasks = dispatcher.get_open_tasks()
        assert len(open_tasks) == 4

    def test_status_transitions(self):
        dispatcher = TaskDispatcher()
        dispatcher.add_task(GENESIS_TASKS[0])
        assignment = dispatcher.assign_task(
            "genesis-001", "node-a", "agent-a", "node-b", "agent-b"
        )
        assert assignment is not None
        assert assignment.status == "assigned"

        dispatcher.mark_submitted(assignment.assignment_id)
        assert dispatcher.get_assignment(assignment.assignment_id).status == "submitted"

        dispatcher.mark_validated(assignment.assignment_id)
        assert dispatcher.get_assignment(assignment.assignment_id).status == "validated"

        dispatcher.mark_rewarded(assignment.assignment_id)
        assert dispatcher.get_assignment(assignment.assignment_id).status == "rewarded"


# ============================================================
# Validator Tests
# ============================================================

class TestValidator:
    @pytest.mark.asyncio
    async def test_validate_basic_result(self):
        """Basic validation of a task result"""
        validator = Validator(node_id="node-b")
        task = get_task_by_id("genesis-001")
        result = (
            "## Code Optimization Report\n\n"
            "The bubble sort has O(n^2) complexity.\n\n"
            "### Optimized Version\n"
            "```python\n"
            "def quick_sort(arr):\n    ...\n"
            "```\n\n"
            "### Complexity Comparison\n"
            "Bubble sort: O(n^2) → Quick sort: O(n log n)\n\n"
            "### Recommendation\n"
            "Use built-in `sorted()` for most cases.\n"
        )

        validation = await validator.validate(
            task=task,
            worker_node_id="node-a",  # Different from validator's node-b
            worker_agent_id="agent-a1",
            result=result,
            assignment_id="assign-001",
        )

        assert validation.total_score > 0
        assert validation.quality_score > 0

    @pytest.mark.asyncio
    async def test_self_validation_blocked(self):
        """CRITICAL: Self-validation is BLOCKED"""
        validator = Validator(node_id="node-a")
        task = get_task_by_id("genesis-001")

        validation = await validator.validate(
            task=task,
            worker_node_id="node-a",  # SAME as validator — VIOLATION
            worker_agent_id="agent-a1",
            result="Some result",
            assignment_id="assign-001",
        )

        assert validation.passed == False
        assert validation.total_score == 0
        assert "SELF-VALIDATION" in validation.feedback.upper()

    @pytest.mark.asyncio
    async def test_validation_scoring(self):
        """Scoring produces reasonable values"""
        validator = Validator(node_id="validator-node")
        task = get_task_by_id("genesis-002")  # Knowledge task

        # Good result
        good_result = (
            "# Agent Economy Protocol\n\n"
            "## 1. What is an Agent Economy Protocol?\n"
            "An Agent Economy Protocol is...\n\n"
            "## 2. What is Proof of Intelligence?\n"
            "PoI is a consensus mechanism where...\n\n"
            "## 3. Comparison with PoW and PoS\n"
            "Key differences: ...\n\n"
            "## 4. Use Cases\n"
            "Example applications include...\n\n"
            "## Analysis\n"
            "An interesting insight is that...\n"
        ) * 3  # Make it substantial

        validation = await validator.validate(
            task=task,
            worker_node_id="other-node",
            worker_agent_id="agent-x",
            result=good_result,
            assignment_id="assign-g",
        )

        assert 0 <= validation.quality_score <= 100
        assert 0 <= validation.verification_score <= 100
        assert 0 <= validation.innovation_score <= 100
        assert validation.total_score > 50  # Good result should pass
        assert validation.passed

    @pytest.mark.asyncio
    async def test_low_quality_result_fails(self):
        """Very poor result should fail validation"""
        validator = Validator(node_id="validator-node")
        task = get_task_by_id("genesis-004")  # Tool dev task

        bad_result = "here is a function: def x(): pass"

        validation = await validator.validate(
            task=task,
            worker_node_id="other-node",
            worker_agent_id="agent-x",
            result=bad_result,
            assignment_id="assign-bad",
        )

        assert validation.total_score < 60  # Should score low
