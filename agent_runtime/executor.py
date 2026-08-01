"""
Agent Runtime — Executor

Executes plan steps sequentially, invoking tools when specified.
Collects step outputs into a final result.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from .llm_client import LLMClient
from .planner import Plan, PlanStep
from .tools import Tool, build_tool_registry

logger = logging.getLogger(__name__)

EXECUTOR_SYSTEM_PROMPT = """You are a Task Executor in the AGT Network.
Your job is to execute a specific step in a task plan and produce output.

Guidelines:
1. Execute the step carefully and thoroughly.
2. Output high-quality, well-structured results.
3. If you're not sure about something, explain your reasoning.
4. Be creative and helpful in your execution."""


@dataclass
class StepResult:
    """Result of executing one plan step"""
    step_id: str
    success: bool
    output: str
    tool_used: str | None = None
    error: str | None = None


@dataclass
class ExecutionResult:
    """Complete execution result for a plan"""
    plan_id: str
    goal: str
    step_results: list[StepResult]
    final_output: str = ""
    success: bool = False


class Executor:
    """
    Plan executor.

    Iterates through plan steps, invoking LLM and tools,
    collecting results into final output.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.tools: dict[str, Tool] = build_tool_registry()

    async def execute(self, plan: Plan) -> ExecutionResult:
        """Execute all steps in a plan"""
        step_results = []
        outputs = []

        for step in plan.steps:
            result = await self._execute_step(step, plan.goal)
            step_results.append(result)

            if result.success:
                outputs.append(f"[{step.step_id}] {result.output}")
            else:
                outputs.append(f"[{step.step_id}] FAILED: {result.error}")

        final_output = "\n\n".join(outputs)
        all_success = all(r.success for r in step_results)

        return ExecutionResult(
            plan_id=plan.plan_id,
            goal=plan.goal,
            step_results=step_results,
            final_output=final_output,
            success=all_success,
        )

    async def _execute_step(self, step: PlanStep, goal: str) -> StepResult:
        """Execute a single plan step"""
        try:
            # If step specifies a tool and it's available, use it
            if step.tool and step.tool in self.tools:
                tool = self.tools[step.tool]
                result_text = tool.func(**step.tool_params)
                return StepResult(
                    step_id=step.step_id,
                    success=True,
                    output=result_text,
                    tool_used=step.tool,
                )

            # Otherwise, use LLM to execute
            prompt = (
                f"TASK GOAL: {goal}\n\n"
                f"CURRENT STEP: {step.action}\n"
                f"Expected output: {step.expected_output}\n\n"
                f"Execute this step and provide the output."
            )

            resp = await self.llm.chat(
                prompt=prompt,
                system=EXECUTOR_SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=2048,
            )

            return StepResult(
                step_id=step.step_id,
                success=True,
                output=resp.content,
            )

        except Exception as e:
            logger.warning(f"Step {step.step_id} failed: {e}")
            return StepResult(
                step_id=step.step_id,
                success=False,
                output="",
                error=str(e),
            )
