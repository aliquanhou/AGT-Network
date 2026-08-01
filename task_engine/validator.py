"""
Task Engine — Validator Agent

Independent Validator that evaluates submitted task results.
The validator MUST be from a different node than the worker.

Validation flow:
    Worker Agent submits result
        ↓
    Validator Agent evaluates quality
        ↓
    Validation Score (0–100)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .tasks import AGTTask

logger = logging.getLogger(__name__)

VALIDATOR_SYSTEM_PROMPT = """You are a Validator Agent in the AGT Network.
Your job is to evaluate task results submitted by Worker Agents.

Rules:
1. Be fair and objective.
2. Evaluate based on the task's validator_instructions.
3. Score from 0-100, where:
   - 90-100: Excellent — exceeds requirements
   - 70-89: Good — meets all requirements
   - 50-69: Adequate — meets most requirements
   - 30-49: Poor — significant gaps
   - 0-29: Inadequate — fails to meet basic requirements
4. Provide specific feedback explaining the score.

Output ONLY valid JSON:
```json
{
  "quality_score": 85,
  "verification_score": 80,
  "innovation_score": 70,
  "feedback": "Detailed explanation...",
  "passed": true
}
```
"""


@dataclass
class ValidationResult:
    """Result of validating a task submission"""
    validator_node_id: str
    validator_agent_id: str
    task_id: str
    assignment_id: str

    # Scores
    quality_score: float  # 0–100: how well the task was done
    verification_score: float  # 0–100: how verifiable the result is
    innovation_score: float  # 0–100: creativity/novelty

    feedback: str = ""
    passed: bool = False

    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total_score(self) -> float:
        """Weighted total validation score"""
        return (
            self.quality_score * 0.5
            + self.verification_score * 0.3
            + self.innovation_score * 0.2
        )


class Validator:
    """
    Task Validator.

    Evaluates task results independently.
    v0.1: Uses heuristic scoring + optional LLM validation.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.validations_performed: int = 0

    async def validate(
        self,
        task: AGTTask,
        worker_node_id: str,
        worker_agent_id: str,
        result: str,
        assignment_id: str,
        validator_agent_id: str = "validator-default",
        llm_client=None,  # Optional LLM for deep validation
    ) -> ValidationResult:
        """
        Validate a task submission.

        Args:
            task: The original task
            worker_node_id: Node that performed the work
            worker_agent_id: Agent that performed the work
            result: The submitted result text
            assignment_id: Assignment ID
            validator_agent_id: This validator's agent ID
            llm_client: Optional LLM client for deeper validation

        Returns:
            ValidationResult with scores
        """
        # Rule: validator cannot be the worker
        if self.node_id == worker_node_id:
            logger.error(
                f"[Validator] SELF-VALIDATION BLOCKED: "
                f"Validator on node {self.node_id} cannot validate "
                f"work from the same node."
            )
            return ValidationResult(
                validator_node_id=self.node_id,
                validator_agent_id=validator_agent_id,
                task_id=task.id,
                assignment_id=assignment_id,
                quality_score=0,
                verification_score=0,
                innovation_score=0,
                feedback="VALIDATION REJECTED: Self-validation is not allowed.",
                passed=False,
            )

        # Heuristic scoring (v0.1 baseline)
        quality = self._score_quality(task, result)
        verification = self._score_verifiability(result)
        innovation = self._score_innovation(task, result)

        feedback_parts = [
            f"Task: {task.name}",
            f"Difficulty: {task.difficulty}/10",
            f"Quality Score: {quality:.1f}/100",
            f"Verification Score: {verification:.1f}/100",
            f"Innovation Score: {innovation:.1f}/100",
        ]

        # Use LLM for deeper validation if available
        if llm_client:
            try:
                llm_feedback = await self._llm_validate(task, result, llm_client)
                feedback_parts.append(f"\nLLM Assessment: {llm_feedback}")
            except Exception as e:
                logger.warning(f"[Validator] LLM validation failed: {e}")

        total = quality * 0.5 + verification * 0.3 + innovation * 0.2
        passed = total >= 50

        feedback = "\n".join(feedback_parts)
        self.validations_performed += 1

        logger.info(
            f"[Validator] Task {task.id}: score={total:.1f}, passed={passed}"
        )

        return ValidationResult(
            validator_node_id=self.node_id,
            validator_agent_id=validator_agent_id,
            task_id=task.id,
            assignment_id=assignment_id,
            quality_score=quality,
            verification_score=verification,
            innovation_score=innovation,
            feedback=feedback,
            passed=passed,
        )

    # ---- heuristic scorers ----

    def _score_quality(self, task: AGTTask, result: str) -> float:
        """Heuristic quality scoring"""
        score = 50.0  # baseline

        # Length check: reasonable output
        if len(result) > 200:
            score += 10
        if len(result) > 500:
            score += 10
        if len(result) > 1000:
            score += 10

        # Structure check: has sections/paragraphs
        if "\n\n" in result:
            score += 5

        # Requirement keyword matching
        req_words = task.requirement.lower().split()
        result_lower = result.lower()
        match_count = sum(1 for w in req_words if len(w) > 3 and w in result_lower)
        score += min(15, match_count * 2)

        return min(100, max(0, score))

    def _score_verifiability(self, result: str) -> float:
        """Heuristic verifiability scoring"""
        score = 50.0

        # Has code blocks (reproducible)
        if "```" in result:
            score += 20

        # Has numbered/named sections
        import re
        sections = re.findall(r'(?:^|\n)(?:\d+\.|[A-Z][a-z]+:)', result)
        score += min(15, len(sections) * 5)

        # Has examples
        if "example" in result.lower():
            score += 10

        return min(100, max(0, score))

    def _score_innovation(self, task: AGTTask, result: str) -> float:
        """Heuristic innovation scoring"""
        score = 30.0  # Lower baseline — innovation is harder

        # Length beyond minimum suggests depth
        if len(result) > 800:
            score += 15
        if len(result) > 2000:
            score += 15

        # Contains analysis/discussion
        analysis_keywords = ["analysis", "insight", "trade-off", "alternative", "however", "interestingly"]
        matches = sum(1 for kw in analysis_keywords if kw in result.lower())
        score += matches * 5

        # High-difficulty tasks get innovation bonus
        score += task.difficulty * 2

        return min(100, max(0, score))

    async def _llm_validate(self, task: AGTTask, result: str, llm_client) -> str:
        """Use LLM for deeper validation"""
        prompt = (
            f"Evaluate this task result:\n\n"
            f"TASK: {task.name}\n"
            f"GOAL: {task.goal}\n"
            f"DIFFICULTY: {task.difficulty}/10\n"
            f"VALIDATION CRITERIA: {task.validator_instructions}\n\n"
            f"SUBMITTED RESULT:\n{result[:3000]}\n\n"
            f"Provide a brief assessment and score justification."
        )
        resp = await llm_client.chat(
            prompt=prompt,
            system=VALIDATOR_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1024,
        )
        return resp.content
