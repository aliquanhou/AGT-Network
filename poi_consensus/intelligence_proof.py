"""
POI Consensus — Intelligence Proof (智能贡献证明)

The core data structure of AGT Network.
An Intelligence Proof records the complete evidence chain of
an Agent's intellectual contribution — not just a score.

Architecture:
    Task → Execution → Validation → IntelligenceProof → Ledger
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ContributionType(str, Enum):
    """Types of intelligence contributions"""
    CODE_CREATION = "code_creation"
    CODE_OPTIMIZATION = "code_optimization"
    KNOWLEDGE_ORGANIZATION = "knowledge_organization"
    CREATIVE_DESIGN = "creative_design"
    TOOL_DEVELOPMENT = "tool_development"
    ANALYSIS = "analysis"
    RESEARCH = "research"


class EvidenceType(str, Enum):
    """Types of contribution evidence"""
    CODE_COMMIT = "code_commit"
    TEST_RESULT = "test_result"
    VALIDATION_FEEDBACK = "validation_feedback"
    USER_FEEDBACK = "user_feedback"
    ARTIFACT_HASH = "artifact_hash"
    BENCHMARK = "benchmark"
    PEER_REVIEW = "peer_review"


@dataclass
class EvidenceItem:
    """A single piece of contribution evidence"""
    type: EvidenceType
    description: str
    content_hash: str  # SHA-256 of the evidence content
    url: str = ""  # Optional external reference
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """Normalize type to EvidenceType enum"""
        if not isinstance(self.type, EvidenceType):
            try:
                self.type = EvidenceType(str(self.type))
            except (ValueError, TypeError):
                self.type = EvidenceType.ARTIFACT_HASH

    def _etype_str(self) -> str:
        """Safe type → string"""
        if isinstance(self.type, EvidenceType):
            return self.type.value
        return str(self.type)

    def to_dict(self) -> dict:
        return {
            "type": self._etype_str(),
            "description": self.description,
            "content_hash": self.content_hash,
            "url": self.url,
            "timestamp": self.timestamp,
        }


@dataclass
class IntelligenceProof:
    """
    Intelligence Proof (PoI) — 智能贡献证明

    Complete record of an Agent's intellectual contribution.
    This is the core asset of the AGT Network, not tokens.
    """

    proof_id: str
    task_id: str

    # Contributor
    agent_id: str
    node_id: str

    task_name: str = ""
    contribution_type: ContributionType = ContributionType.ANALYSIS

    # Scores
    difficulty: int = 1  # Task difficulty (1–10)
    quality_score: float = 0.0  # From Validator
    verification_score: float = 0.0  # From Validator
    innovation_score: float = 0.0  # From Validator

    @property
    def contribution_score(self) -> float:
        """
        PoI Score formula:
        Contribution = Difficulty × Quality × Verification × Innovation

        Normalized to [0, 1000]:
           difficulty_weight * quality * verification * innovation
        where difficulty_weight = difficulty / 10
        """
        diff_weight = self.difficulty / 10.0
        raw = (
            diff_weight
            * (self.quality_score / 100.0)
            * (self.verification_score / 100.0)
            * (self.innovation_score / 100.0)
        )
        return round(raw * 1000.0, 2)

    @property
    def agt_credit(self) -> float:
        """
        AGT Credit from this contribution.

        Credit = contribution_score * task_value / 10

        v0.1: Experimental AGT Credit — NOT a real token.
        Future: mapped to AGT Token on-chain.
        """
        return round(self.contribution_score * self.task_value / 10.0, 2)

    # Task metadata
    task_value: float = 10.0
    task_source: str = "genesis"

    # Evidence chain
    evidence: list[EvidenceItem] = field(default_factory=list)

    # Validator info
    validator_node_id: str = ""
    validator_agent_id: str = ""
    validator_feedback: str = ""

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """Normalize contribution_type to ContributionType enum"""
        if not isinstance(self.contribution_type, ContributionType):
            try:
                self.contribution_type = ContributionType(str(self.contribution_type))
            except (ValueError, TypeError):
                self.contribution_type = ContributionType.ANALYSIS

    def _ct_str(self) -> str:
        """Safe contribution_type → string (handles both enum and raw string)"""
        if isinstance(self.contribution_type, ContributionType):
            return self.contribution_type.value
        if isinstance(self.contribution_type, str):
            return self.contribution_type
        return str(self.contribution_type)

    def to_dict(self) -> dict:
        return {
            "proof_id": self.proof_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "agent_id": self.agent_id,
            "node_id": self.node_id,
            "contribution_type": self._ct_str(),
            "difficulty": self.difficulty,
            "scores": {
                "quality": self.quality_score,
                "verification": self.verification_score,
                "innovation": self.innovation_score,
                "contribution": self.contribution_score,
                "agt_credit": self.agt_credit,
            },
            "task_value": self.task_value,
            "task_source": self.task_source,
            "evidence": [e.to_dict() for e in self.evidence],
            "validator": {
                "node_id": self.validator_node_id,
                "agent_id": self.validator_agent_id,
                "feedback": self.validator_feedback,
            },
            "created_at": self.created_at,
            "content_hash": self.compute_hash(),
        }

    def compute_hash(self) -> str:
        """SHA-256 hash of the core proof content (excluding hash field itself)"""
        core = {
            "proof_id": self.proof_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "node_id": self.node_id,
            "contribution_type": self._ct_str(),
            "contribution_score": self.contribution_score,
            "evidence_hashes": [e.content_hash for e in self.evidence],
            "created_at": self.created_at,
        }
        serialized = json.dumps(core, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> "IntelligenceProof":
        """Restore an IntelligenceProof from its dict representation"""
        evidence = []
        for e in data.get("evidence", []):
            try:
                etype = EvidenceType(e["type"])
            except (ValueError, KeyError):
                etype = EvidenceType.ARTIFACT_HASH
            evidence.append(EvidenceItem(
                type=etype,
                description=e.get("description", ""),
                content_hash=e.get("content_hash", ""),
                url=e.get("url", ""),
                timestamp=e.get("timestamp", ""),
            ))

        ct = ContributionType.ANALYSIS
        try:
            ct = ContributionType(data.get("contribution_type", "analysis"))
        except ValueError:
            pass

        validator = data.get("validator", {})
        scores = data.get("scores", {})

        return cls(
            proof_id=data.get("proof_id", ""),
            task_id=data.get("task_id", ""),
            task_name=data.get("task_name", ""),
            agent_id=data.get("agent_id", ""),
            node_id=data.get("node_id", ""),
            contribution_type=ct,
            difficulty=data.get("difficulty", 1),
            quality_score=scores.get("quality", 0.0),
            verification_score=scores.get("verification", 0.0),
            innovation_score=scores.get("innovation", 0.0),
            task_value=data.get("task_value", 10.0),
            task_source=data.get("task_source", "genesis"),
            evidence=evidence,
            validator_node_id=validator.get("node_id", ""),
            validator_agent_id=validator.get("agent_id", ""),
            validator_feedback=validator.get("feedback", ""),
            created_at=data.get("created_at", ""),
        )

    @classmethod
    def create(
        cls,
        task_id: str,
        task_name: str,
        agent_id: str,
        node_id: str,
        contribution_type: str,
        difficulty: int,
        quality_score: float,
        verification_score: float,
        innovation_score: float,
        task_value: float = 10.0,
        task_source: str = "genesis",
        evidence: list[EvidenceItem] = None,
        validator_node_id: str = "",
        validator_agent_id: str = "",
        validator_feedback: str = "",
    ) -> "IntelligenceProof":
        """Factory: create a complete Intelligence Proof"""
        proof_id = f"poi-{uuid.uuid4().hex[:12]}"

        ct = ContributionType.ANALYSIS
        try:
            ct = ContributionType(contribution_type)
        except ValueError:
            pass

        return cls(
            proof_id=proof_id,
            task_id=task_id,
            task_name=task_name,
            agent_id=agent_id,
            node_id=node_id,
            contribution_type=ct,
            difficulty=difficulty,
            quality_score=quality_score,
            verification_score=verification_score,
            innovation_score=innovation_score,
            task_value=task_value,
            task_source=task_source,
            evidence=evidence or [],
            validator_node_id=validator_node_id,
            validator_agent_id=validator_agent_id,
            validator_feedback=validator_feedback,
        )


# ============================================================
# Evidence Factory
# ============================================================

def make_evidence(
    etype: EvidenceType,
    description: str,
    content: str,
    url: str = "",
) -> EvidenceItem:
    """Create an evidence item, auto-computing the content hash"""
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    return EvidenceItem(
        type=etype,
        description=description,
        content_hash=content_hash,
        url=url,
    )
