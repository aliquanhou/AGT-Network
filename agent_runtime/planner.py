"""
Agent Runtime — Planner

Task planner: breaks down high-level tasks into executable steps.
Uses LLM to decompose a task goal into a plan of sub-steps.
"""

import json
import logging
from dataclasses import dataclass, field

from .llm_client import LLMClient, LLMResponse
from .tools import Tool

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are a Task Planner for the AGT Network agent system.
Your job is to decompose a task goal into concrete, executable steps.

Rules:
1. Each step must be a single, clear action.
2. Steps must be in execution order.
3. If the task requires a tool, specify which tool and its parameters.
4. Output ONLY valid JSON in this format:

```json
{
  "plan_id": "unique-id",
  "goal": "the original goal",
  "steps": [
    {
      "step_id": "step-1",
      "action": "description of what to do",
      "tool": "tool_name or null",
      "tool_params": {},
      "expected_output": "what this step should produce"
    }
  ]
}
```

Available tools: code_analyzer, text_formatter, calculator, searcher."""


@dataclass
class PlanStep:
    """A single step in an execution plan"""
    step_id: str
    action: str
    tool: str | None = None
    tool_params: dict = field(default_factory=dict)
    expected_output: str = ""


@dataclass
class Plan:
    """Execution plan for a task"""
    plan_id: str
    goal: str
    steps: list[PlanStep]
    raw: dict = field(default_factory=dict)


class Planner:
    """
    Task planner using LLM.

    Converts a task goal into a structured execution plan.
    Falls back to a deterministic plan if LLM is unavailable.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def plan(self, goal: str, context: dict = None) -> Plan:
        """Generate execution plan for a task goal"""
        prompt = f"Create an execution plan for this task:\n\nGOAL: {goal}\n"
        if context:
            prompt += f"\nCONTEXT: {json.dumps(context, ensure_ascii=False)}\n"

        try:
            resp = await self.llm.chat(
                prompt=prompt,
                system=PLANNER_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=2048,
            )
            return self._parse_plan(resp.content, goal)
        except Exception as e:
            logger.warning(f"LLM planning failed, using fallback: {e}")
            return self._fallback_plan(goal)

    def _parse_plan(self, content: str, goal: str) -> Plan:
        """Parse LLM response into a Plan object"""
        try:
            # Extract JSON from response (may be wrapped in markdown)
            if "```json" in content:
                start = content.index("```json") + 7
                end = content.index("```", start)
                content = content[start:end]
            elif "```" in content:
                start = content.index("```") + 3
                end = content.index("```", start)
                content = content[start:end]

            data = json.loads(content.strip())

            steps = []
            for s in data.get("steps", []):
                steps.append(PlanStep(
                    step_id=s.get("step_id", f"step-{len(steps)}"),
                    action=s.get("action", ""),
                    tool=s.get("tool"),
                    tool_params=s.get("tool_params", {}),
                    expected_output=s.get("expected_output", ""),
                ))

            return Plan(
                plan_id=data.get("plan_id", "plan-fallback"),
                goal=goal,
                steps=steps,
                raw=data,
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse plan JSON: {e}")
            return self._fallback_plan(goal)

    def _fallback_plan(self, goal: str) -> Plan:
        """Deterministic fallback plan (no LLM needed)"""
        return Plan(
            plan_id="plan-fallback",
            goal=goal,
            steps=[
                PlanStep(
                    step_id="step-1",
                    action=f"Analyze the task: {goal}",
                    tool="searcher",
                    tool_params={"query": goal},
                    expected_output="Understanding of the task requirements",
                ),
                PlanStep(
                    step_id="step-2",
                    action="Execute the core work",
                    tool=None,
                    tool_params={},
                    expected_output="Task output",
                ),
                PlanStep(
                    step_id="step-3",
                    action="Format and verify the output",
                    tool="text_formatter",
                    tool_params={"text": "Task executed successfully.", "format_type": "markdown"},
                    expected_output="Formatted, verified output",
                ),
            ],
        )
