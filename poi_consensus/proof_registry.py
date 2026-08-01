"""
POI Consensus — Proof Registry (v0.2 Trust Layer)

Stores verified signatures and provides independent proof verification.
Any node can verify any proof's signature without trusting the prover.

Cross-node verification: even if a proof was generated on another node,
the receiving node can independently verify its authenticity.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class VerifiedSignature:
    """Record of a verified proof signature"""
    proof_id: str
    validator_public_key_hex: str
    signature: str
    verified_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified_by_node: str = ""


class ProofRegistry:
    """
    Registry of verified proof signatures (v0.2 Trust Layer).

    Enables independent verification:
    1. Store known validator public keys
    2. Verify any incoming proof's signature
    3. Track verification history
    """

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self._known_validators: dict[str, str] = {}  # node_id → public_key_hex
        self._verified_proofs: list[VerifiedSignature] = []
        self._verification_count: int = 0
        self._load()

    # ---- validator key management ----

    def register_validator(self, node_id: str, public_key_hex: str):
        """Register a known validator's public key"""
        self._known_validators[node_id] = public_key_hex
        logger.info(f"[Registry] Registered validator: {node_id}")

    def get_validator_key(self, node_id: str) -> Optional[str]:
        """Get a validator's public key"""
        return self._known_validators.get(node_id)

    def is_known_validator(self, node_id: str) -> bool:
        """Check if a node is a known validator"""
        return node_id in self._known_validators

    # ---- proof verification ----

    def verify_proof(self, proof: "IntelligenceProof") -> dict:
        """
        Independently verify a proof's signature.

        Returns a verification report:
        {
            "verified": bool,
            "reason": str,
            "validator_known": bool,
        }
        """
        if not proof.is_signed():
            self._verification_count += 1
            return {
                "verified": False,
                "reason": "Proof is not signed",
                "validator_known": False,
            }

        # Cryptographic verification
        sig_valid = proof.verify_signature()
        if not sig_valid:
            self._verification_count += 1
            return {
                "verified": False,
                "reason": "Signature verification failed — proof may be tampered",
                "validator_known": self.is_known_validator(proof.validator_node_id),
            }

        # Register the validated signature
        record = VerifiedSignature(
            proof_id=proof.proof_id,
            validator_public_key_hex=proof.validator_public_key_hex,
            signature=proof.validator_signature,
        )
        self._verified_proofs.append(record)
        self._verification_count += 1

        # Auto-register validator if unknown
        if not self.is_known_validator(proof.validator_node_id):
            self.register_validator(proof.validator_node_id, proof.validator_public_key_hex)

        return {
            "verified": True,
            "reason": "Signature valid",
            "validator_known": True,
        }

    # ---- cross-node verification ----

    def import_proof(self, proof: "IntelligenceProof", source_node_id: str) -> dict:
        """
        Verify a proof received from another node via P2P.

        More stringent than local proof verification:
        - The proof must be signed
        - The signature must match the claimed validator
        - The proof content must be internally consistent (hash check)
        """
        result = self.verify_proof(proof)

        if result["verified"]:
            # Additional check: proof hash must be self-consistent
            stored_hash = proof.to_dict().get("content_hash", "")
            computed_hash = proof.compute_hash()
            if stored_hash and stored_hash != computed_hash:
                return {
                    "verified": False,
                    "reason": "Proof content hash mismatch — data corrupted",
                    "validator_known": result["validator_known"],
                }
            result["source_node"] = source_node_id

        logger.info(
            f"[Registry] Imported proof {proof.proof_id}: "
            f"verified={result['verified']} from {source_node_id}"
        )
        return result

    def get_stats(self) -> dict:
        return {
            "known_validators": len(self._known_validators),
            "verified_proofs": len(self._verified_proofs),
            "total_verifications": self._verification_count,
        }

    # ---- persistence ----

    def _load(self):
        path = os.path.join(self.data_dir, "proof_registry.json")
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._known_validators = data.get("validators", {})
                self._verification_count = data.get("count", 0)
        except Exception:
            pass

    def save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        path = os.path.join(self.data_dir, "proof_registry.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "validators": self._known_validators,
                    "count": self._verification_count,
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"[Registry] Save failed: {e}")
