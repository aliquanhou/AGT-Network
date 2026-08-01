"""
AGT Node — Identity & Genesis Identity

Node identity management.
Genesis Identity: records founder/origin, NOT super-admin privileges.

Genesis Identity properties:
- founder_id: who initiated this AGT node
- genesis_timestamp: when the network was born
- contribution_hash: hash of the genesis contribution
- NO special permissions: this is purely a historical record
"""

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NodeIdentity:
    """
    A node's identity in the AGT Network.

    Each node has a unique identity, signed with a key pair (v0.5+).
    v0.1: UUID-based identity with optional founder attribution.
    """

    node_id: str
    node_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    public_key: str = ""  # v0.5: Ed25519 public key
    endpoint: str = ""  # P2P endpoint (host:port)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "created_at": self.created_at,
            "public_key": self.public_key,
            "endpoint": self.endpoint,
        }

    @classmethod
    def create(cls, node_name: str = "", founder_id: str = "") -> "NodeIdentity":
        """Create a new node identity"""
        node_id = f"agt-node-{uuid.uuid4().hex[:8]}"
        identity = cls(
            node_id=node_id,
            node_name=node_name or node_id,
        )
        return identity


@dataclass
class GenesisIdentity:
    """
    Genesis Identity — 创世身份记录

    Records the founding event of this AGT Node / Network.

    IMPORTANT:
        This is NOT a super-admin account.
        It does NOT grant withdrawal rights.
        It does NOT grant special governance power.
        It is purely a historical marker of when this AGT instance began.

    Future:
        Genesis Identity may be referenced for:
        - Network origin attribution
        - Founder recognition (not privilege)
        - Historical integrity verification
    """

    founder_id: str
    genesis_timestamp: str
    genesis_hash: str
    node_id: str = ""
    mission: str = "Build the AGT AI Knowledge Civilization"
    version: str = "v0.1-genesis"

    @classmethod
    def create(cls, founder_id: str, node_id: str, mission: str = None) -> "GenesisIdentity":
        """Create a genesis identity record"""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Hash of founding event
        genesis_data = {
            "founder_id": founder_id,
            "node_id": node_id,
            "timestamp": timestamp,
            "mission": mission or cls.mission,
            "version": cls.version,
        }
        serialized = json.dumps(genesis_data, sort_keys=True, ensure_ascii=False)
        genesis_hash = hashlib.sha256(serialized.encode()).hexdigest()

        return cls(
            founder_id=founder_id,
            genesis_timestamp=timestamp,
            genesis_hash=genesis_hash,
            node_id=node_id,
            mission=mission or cls.mission,
        )

    def to_dict(self) -> dict:
        return {
            "founder_id": self.founder_id,
            "genesis_timestamp": self.genesis_timestamp,
            "genesis_hash": self.genesis_hash,
            "node_id": self.node_id,
            "mission": self.mission,
            "version": self.version,
        }
