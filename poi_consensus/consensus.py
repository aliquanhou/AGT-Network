"""
POI Consensus — Consensus Engine

Consensus flow:
    Worker Agent submits result
        ↓
    Validator Agent evaluates
        ↓
    Consensus Engine confirms
        ↓
    Intelligence Proof generated
        ↓
    Reward credit computed
        ↓
    Ledger entry created
        ↓
    Reputation updated

v0.1: Single-validator consensus (no BFT/multi-party needed).
v0.5+: Multi-validator BFT consensus.
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable

from .intelligence_proof import IntelligenceProof
from .scorer import PoIScorer, ContributionScore
from task_engine.tasks import AGTTask
from task_engine.validator import ValidationResult, Validator

logger = logging.getLogger(__name__)


@dataclass
class ConsensusResult:
    """Output of the consensus process"""
    proof: IntelligenceProof
    score: ContributionScore
    confirmed: bool
    reward_credit: float
    consensus_id: str = ""
    confirmed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConsensusEngine:
    """
    AGT Consensus Engine.

    Orchestrates the flow from validation to reward.
    v0.1: Direct consensus (single validator).
    Future: multi-party Byzantine fault-tolerant consensus.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.scorer = PoIScorer()
        self.validator = Validator(node_id=node_id)

        # v0.2: Signing key for proof signatures
        self._signing_key_pair = None  # KeyPair for signing proofs

        # Callbacks
        self._on_proof_generated: Optional[Callable] = None
        self._on_reward: Optional[Callable] = None

        # Stats
        self.proofs_confirmed: int = 0
        self.total_credit_issued: float = 0.0

    def set_signing_key(self, key_pair):
        """
        v0.2: Set the Ed25519 key pair used to sign IntelligenceProofs.

        Without a signing key, proofs will be unsigned (v0.1 compatibility mode).
        """
        self._signing_key_pair = key_pair

    def on_proof_generated(self, callback: Callable):
        """Register callback when an Intelligence Proof is generated"""
        self._on_proof_generated = callback

    def on_reward(self, callback: Callable):
        """Register callback when reward credit is issued"""
        self._on_reward = callback

    async def process_contribution(
        self,
        task: AGTTask,
        agent_id: str,
        worker_node_id: str,
        result: str,
        assignment_id: str,
        validator_agent_id: str = "validator-default",
        llm_client=None,
    ) -> ConsensusResult:
        """
        Full consensus pipeline:

        1. Validate the result
        2. Compute contribution score
        3. Build Intelligence Proof
        4. Confirm consensus
        5. Issue reward credit

        Args:
            task: The original task
            agent_id: Worker agent ID
            worker_node_id: Node that ran the worker
            result: Worker's output
            assignment_id: Task assignment ID
            validator_agent_id: Validator agent ID
            llm_client: Optional LLM for validation

        Returns:
            ConsensusResult with proof and reward
        """
        import uuid

        # Step 1: Validate
        # v0.1: For single-node testing, allow same-node validation
        # by creating a virtual validator identity when needed
        if worker_node_id == self.node_id:
            logger.info(
                "[Consensus] v0.1 single-node mode: "
                "validator runs on same node as worker (local testing)"
            )
            # Create a virtual validator for same-node testing
            virtual_validator = Validator(node_id=f"{self.node_id}-validator")
            validation = await virtual_validator.validate(
                task=task,
                worker_node_id=worker_node_id,
                worker_agent_id=agent_id,
                result=result,
                assignment_id=assignment_id,
                validator_agent_id=validator_agent_id,
                llm_client=llm_client,
            )
        else:
            validation = await self.validator.validate(
                task=task,
                worker_node_id=worker_node_id,
                worker_agent_id=agent_id,
                result=result,
                assignment_id=assignment_id,
                validator_agent_id=validator_agent_id,
                llm_client=llm_client,
            )

        if not validation.passed:
            logger.info(
                f"[Consensus] Validation failed for task {task.id}: "
                f"score={validation.total_score:.1f}"
            )
            # Still build proof (even failures are recorded)
            proof = self.scorer.build_proof(
                task, validation, agent_id, worker_node_id, result
            )
            score = self.scorer.compute_score(task, validation)
            return ConsensusResult(
                proof=proof,
                score=score,
                confirmed=False,
                reward_credit=0.0,
                consensus_id=f"cs-{uuid.uuid4().hex[:8]}",
            )

        # Step 2–3: Build proof
        proof = self.scorer.build_proof(
            task, validation, agent_id, worker_node_id, result
        )
        score = self.scorer.compute_score(task, validation)

        # v0.2: Sign the proof with the validator's Ed25519 key
        if self._signing_key_pair:
            proof.sign(self._signing_key_pair)
            logger.info(f"[Consensus] Proof {proof.proof_id} signed by validator")

        # Step 4: Confirm
        confirmed = score.final_score > 0
        reward = score.agt_credit if confirmed else 0.0

        consensus_id = f"cs-{uuid.uuid4().hex[:8]}"

        self.proofs_confirmed += 1
        self.total_credit_issued += reward

        logger.info(
            f"[Consensus] {consensus_id}: "
            f"Task={task.id}, "
            f"Score={score.final_score:.1f}, "
            f"Credit={reward:.1f}, "
            f"Confirmed={confirmed}"
        )

        # Callbacks
        if self._on_proof_generated and confirmed:
            self._on_proof_generated(proof)
        if self._on_reward and confirmed:
            self._on_reward(agent_id, reward)

        return ConsensusResult(
            proof=proof,
            score=score,
            confirmed=confirmed,
            reward_credit=reward,
            consensus_id=consensus_id,
        )
