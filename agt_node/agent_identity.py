"""
AGT Node — Agent Identity (v0.2 Trust Layer)

Agent identity with cryptographic binding to owner node,
capability profiles, and Soulbound Reputation support.

Key concepts:
1. Agent ID = SHA-256(node_pubkey + creation_index)[:16] — globally unique, verifiable
2. CapabilityProfile — what the agent is good at (Python, Research, etc.)
3. Soulbound — reputation cannot be transferred or purchased
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class CapabilityDomain(str, Enum):
    """Domains an agent can have capability in"""
    PYTHON = "python"
    RESEARCH = "research"
    MATH = "math"
    CODE_REVIEW = "code_review"
    TECHNICAL_WRITING = "technical_writing"
    CREATIVE_DESIGN = "creative_design"
    DATA_ANALYSIS = "data_analysis"
    SYSTEM_ARCHITECTURE = "system_architecture"


@dataclass
class CapabilityProfile:
    """
    What an agent is capable of, rated 1-5 stars.

    Built from contribution history — not self-declared.
    Each completed task in a domain updates the rating.
    """

    ratings: dict[str, float] = field(default_factory=lambda: {
        "python": 1.0,
        "research": 1.0,
        "math": 1.0,
        "code_review": 1.0,
        "technical_writing": 1.0,
        "creative_design": 1.0,
        "data_analysis": 1.0,
        "system_architecture": 1.0,
    })

    def stars(self, domain: str) -> int:
        """Get star rating (1-5) for a domain"""
        raw = self.ratings.get(domain, 1.0)
        return min(5, max(1, round(raw)))

    def update_from_contribution(
        self,
        contribution_type: str,
        quality_score: float,
    ):
        """
        Update capability based on a verified contribution.

        High-quality completions in a domain increase capability.
        Quality score > 80 → stronger update.
        """
        domain_map = {
            "code_optimization": "python",
            "code_creation": "python",
            "knowledge_organization": "research",
            "creative_design": "creative_design",
            "tool_development": "python",
            "analysis": "data_analysis",
            "research": "research",
        }

        domain = domain_map.get(contribution_type)
        if not domain:
            return

        old = self.ratings.get(domain, 1.0)
        # Quality-weighted increment: higher quality → faster growth
        increment = 0.3 + (quality_score / 100.0) * 0.5
        self.ratings[domain] = min(5.0, old + increment)

    def to_dict(self) -> dict:
        return {
            domain: {
                "rating": round(rating, 2),
                "stars": self.stars(domain),
            }
            for domain, rating in self.ratings.items()
        }

    def summary(self) -> dict:
        """Summary of top capabilities"""
        top = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        return {
            domain: self.stars(domain)
            for domain, _ in top[:3]
        }


# ============================================================
# Agent Identity (v0.2)
# ============================================================

@dataclass
class AgentIdentity:
    """
    Cryptographic agent identity (v0.2 Trust Layer).

    Unlike v0.1 UUIDs, v0.2 agent IDs are derived from the
    owner node's Ed25519 public key, making the agent → node
    binding cryptographically verifiable.

    Also includes:
    - CapabilityProfile (earned through contributions)
    - Soulbound flags (non-transferable, non-purchasable)
    - Creation record
    """

    agent_id: str
    owner_node_id: str
    owner_public_key_hex: str  # Node's Ed25519 public key
    creation_index: int  # Which agent on this node (0, 1, 2, ...)
    name: str = ""

    # Soulbound
    soulbound: bool = True  # Always True — cannot transfer

    # Capabilities
    capability: CapabilityProfile = field(default_factory=CapabilityProfile)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "owner_node_id": self.owner_node_id,
            "owner_public_key": self.owner_public_key_hex,
            "creation_index": self.creation_index,
            "name": self.name,
            "soulbound": self.soulbound,
            "capability": self.capability.to_dict(),
            "created_at": self.created_at,
        }

    @staticmethod
    def derive_id(public_key_hex: str, agent_index: int) -> str:
        """
        Derive a unique, verifiable agent ID from the node's public key.

        Anyone can verify: agent belongs to node with this public key.
        """
        seed = f"{public_key_hex}{agent_index}".encode("utf-8")
        return hashlib.sha256(seed).hexdigest()[:16]

    @staticmethod
    def verify_ownership(
        agent_id: str,
        public_key_hex: str,
        agent_index: int,
    ) -> bool:
        """
        Verify that an agent_id genuinely belongs to a node with
        the given public key and creation index.
        """
        expected = AgentIdentity.derive_id(public_key_hex, agent_index)
        return expected == agent_id

    @classmethod
    def create(
        cls,
        node_identity: "NodeIdentity",
        agent_index: int,
        name: str = "",
    ) -> "AgentIdentity":
        """Create a new agent identity bound to a node"""
        agent_id = cls.derive_id(node_identity.public_key_hex, agent_index)

        identity = cls(
            agent_id=agent_id,
            owner_node_id=node_identity.node_id,
            owner_public_key_hex=node_identity.public_key_hex,
            creation_index=agent_index,
            name=name or f"agent-{agent_id[:6]}",
        )
        return identity
