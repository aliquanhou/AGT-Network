"""
POI Consensus — Contribution Scorer

Computes the Intelligence Contribution Score from task and validation data.

Formula:
    Contribution Score = Difficulty × Quality × Verification × Innovation

Normalized to [0, 1000] range.
Maps to AGT Credit for reward distribution.
"""

import logging
from dataclasses import dataclass

from .intelligence_proof import IntelligenceProof, EvidenceItem, make_evidence
from task_engine.tasks import AGTTask
from task_engine.validator import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ContributionScore:
    """Intermediate scoring output"""
    difficulty_weight: float  # difficulty / 10
    quality_factor: float  # quality_score / 100
    verification_factor: float  # verification_score / 100
    innovation_factor: float  # innovation_score / 100
    raw_score: float  # product × 1000
    final_score: float  # clamped [0, 1000]
    agt_credit: float  # final_score × task_value / 10


class PoIScorer:
    """
    Proof of Intelligence Scorer.

    Converts task execution + validation into a contribution score.
    Also builds the evidence chain for the Intelligence Proof.
    """

    @staticmethod
    def compute_score(
        task: AGTTask,
        validation: ValidationResult,
    ) -> ContributionScore:
        """
        Compute contribution score from task and validation.

        Args:
            task: The original task definition
            validation: Validator's assessment

        Returns:
            ContributionScore with all factors
        """
        difficulty_weight = task.difficulty / 10.0
        quality_factor = validation.quality_score / 100.0
        verification_factor = validation.verification_score / 100.0
        innovation_factor = validation.innovation_score / 100.0

        raw = (
            difficulty_weight
            * quality_factor
            * verification_factor
            * innovation_factor
            * 1000.0
        )

        final = max(0.0, min(1000.0, raw))
        credit = round(final * task.value / 10.0, 2)

        return ContributionScore(
            difficulty_weight=difficulty_weight,
            quality_factor=quality_factor,
            verification_factor=verification_factor,
            innovation_factor=innovation_factor,
            raw_score=round(raw, 2),
            final_score=round(final, 2),
            agt_credit=credit,
        )

    @staticmethod
    def build_proof(
        task: AGTTask,
        validation: ValidationResult,
        agent_id: str,
        node_id: str,
        result_content: str,
    ) -> IntelligenceProof:
        """
        Build a complete Intelligence Proof from task execution data.

        Includes:
        - Score computation
        - Evidence chain generation
        - Validator record
        """
        score = PoIScorer.compute_score(task, validation)

        # Build evidence chain
        evidence: list[EvidenceItem] = []

        # 1. Artifact hash (the output itself)
        evidence.append(make_evidence(
            "artifact_hash",
            f"Task execution output for {task.id}",
            result_content,
        ))

        # 2. Validation feedback
        evidence.append(make_evidence(
            "validation_feedback",
            f"Validator assessment for task {task.id}",
            validation.feedback,
        ))

        # 3. Task requirement
        evidence.append(make_evidence(
            "benchmark",
            f"Task requirements: {task.requirement[:200]}",
            task.requirement,
        ))

        # Determine contribution type from task type
        contrib_type = task.task_type.value

        proof = IntelligenceProof.create(
            task_id=task.id,
            task_name=task.name,
            agent_id=agent_id,
            node_id=node_id,
            contribution_type=contrib_type,
            difficulty=task.difficulty,
            quality_score=validation.quality_score,
            verification_score=validation.verification_score,
            innovation_score=validation.innovation_score,
            task_value=task.value,
            task_source=task.source.value,
            evidence=evidence,
            validator_node_id=validation.validator_node_id,
            validator_agent_id=validation.validator_agent_id,
            validator_feedback=validation.feedback,
        )

        logger.info(
            f"[PoI] Proof {proof.proof_id}: "
            f"score={proof.contribution_score:.1f}, "
            f"credit={proof.agt_credit:.1f}, "
            f"evidence={len(evidence)} items"
        )

        return proof
