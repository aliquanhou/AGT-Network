"""
AGT Node — Identity & Genesis Identity (v0.2 Trust Layer)

Node identity with Ed25519 key pairs.
Genesis Identity: founder record, NOT admin privileges.

v0.2 upgrades:
- Ed25519 key pair generation on node start
- Public key embedded in NodeIdentity
- Agent identity derived from node public key
- Genesis proof is the first Intelligence Proof (unified system)
"""

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


# ============================================================
# Ed25519 Key Management
# ============================================================

@dataclass
class KeyPair:
    """Ed25519 key pair for node identity"""
    private_key: Ed25519PrivateKey
    public_key_bytes: bytes
    public_key_hex: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def generate(cls) -> "KeyPair":
        """Generate a new Ed25519 key pair"""
        sk = Ed25519PrivateKey.generate()
        pk_bytes = sk.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return cls(
            private_key=sk,
            public_key_bytes=pk_bytes,
            public_key_hex=pk_bytes.hex(),
        )

    def sign(self, message: bytes) -> bytes:
        """Sign a message with the private key (64-byte Ed25519 signature)"""
        return self.private_key.sign(message)

    def sign_string(self, message: str) -> str:
        """Sign a string message, return hex-encoded signature"""
        return self.private_key.sign(message.encode("utf-8")).hex()

    @staticmethod
    def verify(public_key_hex: str, message: bytes, signature: bytes) -> bool:
        """Verify a signature against a public key"""
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
        try:
            pk_bytes = bytes.fromhex(public_key_hex)
            pk = Ed25519PublicKey.from_public_bytes(pk_bytes)
            pk.verify(signature, message)
            return True
        except (InvalidSignature, ValueError, Exception):
            return False

    @staticmethod
    def verify_string(public_key_hex: str, message: str, signature_hex: str) -> bool:
        """Verify a hex-encoded signature against a string message"""
        try:
            return KeyPair.verify(
                public_key_hex,
                message.encode("utf-8"),
                bytes.fromhex(signature_hex),
            )
        except Exception:
            return False

    # ---- persistence ----

    def save_private_key(self, path: str):
        """Save private key to file (restricted permissions)"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        with open(path, "wb") as f:
            f.write(pem)
        # Best-effort restrict permissions on Unix
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass

    @classmethod
    def load_private_key(cls, path: str) -> Optional["KeyPair"]:
        """Load private key from file"""
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                sk = serialization.load_pem_private_key(f.read(), password=None)
            pk_bytes = sk.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            return cls(
                private_key=sk,
                public_key_bytes=pk_bytes,
                public_key_hex=pk_bytes.hex(),
            )
        except Exception as e:
            logger.error(f"Failed to load key: {e}")
            return None


# ============================================================
# Node Identity (v0.2)
# ============================================================

@dataclass
class NodeIdentity:
    """
    A node's identity in the AGT Network (v0.2).

    Each node generates an Ed25519 key pair on first launch.
    The public key serves as the node's cryptographic identity.
    """

    node_id: str
    node_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    public_key_hex: str = ""  # Ed25519 public key (64 hex chars)
    endpoint: str = ""  # P2P endpoint (host:port)

    # Internal (not serialized)
    _key_pair: Optional[KeyPair] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "created_at": self.created_at,
            "public_key": self.public_key_hex,
            "endpoint": self.endpoint,
        }

    def sign(self, message: str) -> str:
        """Sign a message with this node's private key"""
        if not self._key_pair:
            raise ValueError("No private key available for signing")
        return self._key_pair.sign_string(message)

    def derive_agent_id(self, agent_index: int) -> str:
        """
        Derive a cryptographically bound agent ID from the node's public key.

        agent_id = SHA-256(node_public_key + agent_index)[:16]
        """
        seed = f"{self.public_key_hex}{agent_index}".encode("utf-8")
        return hashlib.sha256(seed).hexdigest()[:16]

    @classmethod
    def create(
        cls,
        node_name: str = "",
        founder_id: str = "",
        data_dir: str = "./data",
    ) -> "NodeIdentity":
        """Create a new node identity with Ed25519 key pair"""
        # Generate or load key pair
        key_path = os.path.join(data_dir, "node_key.pem")
        key_pair = KeyPair.load_private_key(key_path)

        if key_pair is None:
            key_pair = KeyPair.generate()
            key_pair.save_private_key(key_path)
            logger.info(f"[Identity] New Ed25519 key pair generated")
        else:
            logger.info(f"[Identity] Existing Ed25519 key pair loaded")

        node_id = f"agt-node-{key_pair.public_key_hex[:12]}"

        identity = cls(
            node_id=node_id,
            node_name=node_name or node_id,
            public_key_hex=key_pair.public_key_hex,
            _key_pair=key_pair,
        )
        return identity

    @property
    def key_pair(self) -> Optional[KeyPair]:
        return self._key_pair


# ============================================================
# Genesis Identity (v0.2 — unchanged from v0.1)
# ============================================================

@dataclass
class GenesisIdentity:
    """
    Genesis Identity — 创世身份记录

    Records the founding event of this AGT Node / Network.

    IMPORTANT:
        This is NOT a super-admin account.
        It is a historical record of the network's origin.
        The genesis contribution (block 0) is an Intelligence Proof
        in the same ledger as every other contribution.
    """

    founder_id: str
    genesis_timestamp: str
    genesis_hash: str
    node_id: str = ""
    mission: str = "Build the AGT AI Knowledge Civilization"
    version: str = "v0.2-trust-layer"

    @classmethod
    def create(cls, founder_id: str, node_id: str, mission: str = None) -> "GenesisIdentity":
        """Create a genesis identity record"""
        timestamp = datetime.now(timezone.utc).isoformat()

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
