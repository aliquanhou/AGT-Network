"""
Tests: Agent Runtime — LLM Client + Agent + Tools + Planner + Executor

Verifies:
- LLM client interface consistency
- Tool execution (no LLM needed)
- Planner fallback (deterministic)
- Agent task lifecycle
"""

import pytest

from agent_runtime.llm_client import (
    LLMClient,
    LLMResponse,
    Provider,
    create_llm_client,
)
from agent_runtime.tools import (
    Tool,
    build_tool_registry,
    tool_code_analyzer,
    tool_text_formatter,
    tool_calculator,
    tool_searcher,
)
from agent_runtime.planner import Planner, Plan, PlanStep
from agent_runtime.executor import Executor, StepResult, ExecutionResult
from agent_runtime.agent import AGTAgent, MemoryEntry, TaskResult


# ============================================================
# LLM Client Tests (no API key needed for unit tests)
# ============================================================

class TestLLMClient:
    def test_provider_enum(self):
        assert Provider.DEEPSEEK == "deepseek"
        assert Provider.OPENAI == "openai"
        assert Provider.CLAUDE == "claude"
        assert Provider.OLLAMA == "ollama"

    def test_llm_response(self):
        resp = LLMResponse(
            content="Hello world",
            model="test-model",
            usage={"total_tokens": 10},
        )
        assert resp.content == "Hello world"
        assert resp.finish_reason == "stop"

    def test_create_client_missing_key(self):
        """Missing API key raises for cloud providers"""
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            create_llm_client("deepseek", api_key="")

    def test_create_client_ollama_no_key_needed(self):
        """Ollama doesn't need API key"""
        client = create_llm_client("ollama", base_url="http://localhost:9999")
        assert client is not None
        assert client.model == "llama3.2"

    def test_create_client_invalid_provider(self):
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_llm_client("unknown")


# ============================================================
# Tool Tests (no LLM needed)
# ============================================================

class TestTools:
    def test_code_analyzer(self):
        result = tool_code_analyzer("def hello():\n    print('hi')\n\n# comment")
        assert "Total lines" in result
        assert "4" in result

    def test_code_analyzer_complexity(self):
        code = "x = 1\n" * 300
        result = tool_code_analyzer(code)
        assert "MEDIUM" in result

    def test_text_formatter_markdown(self):
        result = tool_text_formatter("  hello  \n\n  world  ", "markdown")
        assert result == "hello\n\nworld"

    def test_text_formatter_json(self):
        result = tool_text_formatter("hello world", "json")
        import json
        data = json.loads(result)
        assert data["content"] == "hello world"

    def test_calculator(self):
        result = tool_calculator("2 + 3 * 4")
        assert "14" in result

    def test_calculator_math_funcs(self):
        result = tool_calculator("sqrt(16)")
        assert "4.0" in result

    def test_calculator_unsafe_blocked(self):
        result = tool_calculator("__import__('os').system('dir')")
        assert "Error" in result

    def test_searcher(self):
        result = tool_searcher("test query")
        assert "test query" in result.lower()
        assert "v0.1" in result

    def test_tool_registry(self):
        registry = build_tool_registry()
        assert "code_analyzer" in registry
        assert "text_formatter" in registry
        assert "calculator" in registry
        assert "searcher" in registry

    def test_tool_to_openai_spec(self):
        tool = Tool(
            name="test",
            description="A test tool",
            parameters={"type": "object", "properties": {"x": {"type": "string"}}},
            func=lambda x: x,
        )
        spec = tool.to_openai_spec()
        assert spec["type"] == "function"
        assert spec["function"]["name"] == "test"


# ============================================================
# Planner Tests (fallback mode, no LLM)
# ============================================================

class TestPlanner:
    def test_fallback_plan(self):
        planner = Planner(llm=None)  # Will use fallback
        plan = planner._fallback_plan("Test goal")
        assert plan.goal == "Test goal"
        assert len(plan.steps) == 3
        assert plan.steps[0].tool == "searcher"

    def test_plan_step_dataclass(self):
        step = PlanStep(
            step_id="s1",
            action="Do something",
            tool="calculator",
            tool_params={"expression": "1+1"},
            expected_output="2",
        )
        assert step.step_id == "s1"
        assert step.tool == "calculator"


# ============================================================
# Executor Tests (tool-only, no LLM)
# ============================================================

class TestExecutor:
    @pytest.mark.asyncio
    async def test_execute_tool_step(self):
        """Execute a step that uses a built-in tool"""
        executor = Executor(llm=None)
        plan = Plan(
            plan_id="test-plan",
            goal="Calculate something",
            steps=[
                PlanStep(
                    step_id="s1",
                    action="Calculate 10*5",
                    tool="calculator",
                    tool_params={"expression": "10*5"},
                )
            ],
        )
        result = await executor.execute(plan)
        assert result.success
        assert "50" in result.final_output

    @pytest.mark.asyncio
    async def test_execute_multiple_steps(self):
        """Execute multiple tool-based steps"""
        executor = Executor(llm=None)
        plan = Plan(
            plan_id="multi",
            goal="Code and format",
            steps=[
                PlanStep(
                    step_id="s1",
                    action="Analyze code",
                    tool="code_analyzer",
                    tool_params={"code": "def f():\n  pass"},
                ),
                PlanStep(
                    step_id="s2",
                    action="Format output",
                    tool="text_formatter",
                    tool_params={"text": "  hello world  ", "format_type": "plain"},
                ),
            ],
        )
        result = await executor.execute(plan)
        assert result.success
        assert "Code Analysis" in result.final_output
        assert "hello world" in result.final_output


# ============================================================
# Agent Tests
# ============================================================

class MockLLMClient(LLMClient):
    """Mock LLM for testing Agent lifecycle"""
    async def chat(self, prompt, system=None, temperature=0.7, max_tokens=4096, **kwargs):
        return LLMResponse(
            content=f"Mock response for: {prompt[:50]}...",
            model="mock",
        )


class TestAgent:
    @pytest.mark.asyncio
    async def test_agent_creation(self):
        agent = AGTAgent(agent_id="agent-001", llm_client=MockLLMClient())
        status = agent.status()
        assert status["agent_id"] == "agent-001"
        assert status["tasks_completed"] == 0
        assert "calculator" in status["tools"]

    @pytest.mark.asyncio
    async def test_agent_run_task(self):
        agent = AGTAgent(agent_id="agent-test", llm_client=MockLLMClient())
        task = {
            "id": "task-001",
            "goal": "Test task goal",
            "difficulty": 3,
        }
        result = await agent.run_task(task)
        assert result.agent_id == "agent-test"
        assert result.task_id == "task-001"
        assert result.duration_seconds >= 0
        assert agent.tasks_completed == 1

    @pytest.mark.asyncio
    async def test_agent_memory(self):
        agent = AGTAgent(agent_id="agent-mem", llm_client=MockLLMClient())
        task = {"id": "t1", "goal": "Test memory"}

        await agent.run_task(task)
        memories = agent.recall("task")
        assert len(memories) == 1
        assert "t1" in memories[0].content

    @pytest.mark.asyncio
    async def test_agent_add_reward(self):
        agent = AGTAgent(agent_id="agent-rw", llm_client=MockLLMClient())
        agent.add_reward(50.0)
        assert agent.total_reward == 50.0

        memories = agent.recall("observation")
        assert len(memories) == 1
        assert memories[0].metadata["reward"] == 50.0
