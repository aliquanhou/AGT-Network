"""
Tests: v0.2 Identity Layer — Ed25519 Key Pairs + Agent Identity Binding

Verifies:
- Ed25519 key pair generation + sign/verify
- Key persistence (load from disk)
- NodeIdentity with public key
- AgentIdentity derivation from node public key
- Ownership verification
- CapabilityProfile updates
- Soulbound guarantees
"""

import os
import pytest
import tempfile

from agt_node.identity import KeyPair, NodeIdentity, GenesisIdentity
from agt_node.agent_identity import AgentIdentity, CapabilityProfile, CapabilityDomain


# ============================================================
# KeyPair Tests
# ============================================================

class TestKeyPair:
    def test_generate_key_pair(self):
        """Generate Ed25519 key pair"""
        kp = KeyPair.generate()
        assert len(kp.public_key_hex) == 64  # Ed25519 = 32 bytes = 64 hex chars
        assert kp.public_key_bytes is not None

    def test_sign_and_verify(self):
        """Sign a message and verify the signature"""
        kp = KeyPair.generate()
        message = b"AGT Network v0.2 Trust Layer"
        signature = kp.sign(message)

        # Valid signature
        assert KeyPair.verify(kp.public_key_hex, message, signature)

        # Tampered message fails
        assert not KeyPair.verify(kp.public_key_hex, b"tampered message", signature)

        # Tampered signature fails
        tampered = bytearray(signature)
        tampered[0] ^= 1
        assert not KeyPair.verify(kp.public_key_hex, message, bytes(tampered))

        # Wrong public key fails
        kp2 = KeyPair.generate()
        assert not KeyPair.verify(kp2.public_key_hex, message, signature)

    def test_sign_string_and_verify(self):
        """Sign string message, verify hex-encoded signature"""
        kp = KeyPair.generate()
        sig_hex = kp.sign_string("AGT Genesis")
        assert KeyPair.verify_string(kp.public_key_hex, "AGT Genesis", sig_hex)
        assert not KeyPair.verify_string(kp.public_key_hex, "AGT Tampered", sig_hex)

    def test_each_key_pair_is_unique(self):
        """Each generated key pair is different"""
        kp1 = KeyPair.generate()
        kp2 = KeyPair.generate()
        assert kp1.public_key_hex != kp2.public_key_hex

    def test_key_persistence(self):
        """Save and load private key from disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "node_key.pem")
            kp1 = KeyPair.generate()
            kp1.save_private_key(path)

            kp2 = KeyPair.load_private_key(path)
            assert kp2 is not None
            assert kp2.public_key_hex == kp1.public_key_hex

            # Key loaded from disk can sign
            sig = kp2.sign(b"test")
            assert KeyPair.verify(kp2.public_key_hex, b"test", sig)

    def test_load_nonexistent_key(self):
        """Loading a nonexistent key file returns None"""
        kp = KeyPair.load_private_key("/nonexistent/path/key.pem")
        assert kp is None


# ============================================================
# NodeIdentity Tests
# ============================================================

class TestNodeIdentity:
    def test_create_with_key_pair(self):
        """NodeIdentity.create() generates Ed25519 key pair"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ident = NodeIdentity.create(
                node_name="Test Node",
                data_dir=tmpdir,
            )
            assert ident.public_key_hex != ""
            assert len(ident.public_key_hex) == 64
            assert ident.node_id.startswith("agt-node-")
            assert ident._key_pair is not None

    def test_sign_with_node_identity(self):
        """Node identity can sign messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ident = NodeIdentity.create(node_name="Test", data_dir=tmpdir)
            sig = ident.sign("test message")
            assert KeyPair.verify_string(ident.public_key_hex, "test message", sig)

    def test_derive_agent_id_deterministic(self):
        """Agent ID derivation is deterministic"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ident = NodeIdentity.create(node_name="Test", data_dir=tmpdir)
            id1 = ident.derive_agent_id(0)
            id2 = ident.derive_agent_id(0)
            assert id1 == id2  # Same index → same ID

    def test_derive_agent_id_unique_per_index(self):
        """Different indices produce different agent IDs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ident = NodeIdentity.create(node_name="Test", data_dir=tmpdir)
            id0 = ident.derive_agent_id(0)
            id1 = ident.derive_agent_id(1)
            assert id0 != id1

    def test_persist_and_reload_identity(self):
        """Node identity persists across restarts (same key)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ident1 = NodeIdentity.create(node_name="Node", data_dir=tmpdir)
            pk1 = ident1.public_key_hex

            # Simulate restart: create again → loads existing key
            ident2 = NodeIdentity.create(node_name="Node", data_dir=tmpdir)
            assert ident2.public_key_hex == pk1


# ============================================================
# AgentIdentity Tests (v0.2)
# ============================================================

class TestAgentIdentity:
    @pytest.fixture
    def node_ident(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield NodeIdentity.create(node_name="Test", data_dir=tmpdir)

    def test_create_agent_identity(self, node_ident):
        """Agent identity is cryptographically bound to node"""
        agent = AgentIdentity.create(node_ident, 0, name="test-agent")
        assert agent.agent_id != ""
        assert len(agent.agent_id) == 16  # SHA-256 hex[:16]
        assert agent.soulbound == True
        assert agent.creation_index == 0
        assert agent.owner_public_key_hex == node_ident.public_key_hex

    def test_agent_id_derivation(self):
        """Agent ID = SHA-256(pubkey + index)[:16]"""
        pk = "a" * 64
        id0 = AgentIdentity.derive_id(pk, 0)
        id1 = AgentIdentity.derive_id(pk, 1)
        assert id0 != id1

    def test_verify_ownership(self):
        """Ownership can be cryptographically verified"""
        pk = "b" * 64
        agent_id = AgentIdentity.derive_id(pk, 3)
        assert AgentIdentity.verify_ownership(agent_id, pk, 3)
        assert not AgentIdentity.verify_ownership(agent_id, pk, 2)  # Wrong index
        assert not AgentIdentity.verify_ownership(agent_id, "c" * 64, 3)  # Wrong key

    def test_different_nodes_produce_different_ids(self, node_ident):
        """Agents from different nodes have different IDs"""
        pk1 = node_ident.public_key_hex
        pk2 = KeyPair.generate().public_key_hex

        id1 = AgentIdentity.derive_id(pk1, 0)
        id2 = AgentIdentity.derive_id(pk2, 0)
        assert id1 != id2

    def test_to_dict(self, node_ident):
        """Agent identity serialization"""
        agent = AgentIdentity.create(node_ident, 0, name="dict-test")
        d = agent.to_dict()
        assert d["agent_id"] == agent.agent_id
        assert d["owner_public_key"] == node_ident.public_key_hex
        assert d["soulbound"] == True
        assert "capability" in d


# ============================================================
# Capability Profile Tests
# ============================================================

class TestCapabilityProfile:
    def test_initial_capabilities(self):
        """New agent starts with 1-star in all domains"""
        profile = CapabilityProfile()
        for domain in CapabilityDomain:
            assert profile.stars(domain.value) == 1

    def test_update_from_contribution(self):
        """Capability improves with high-quality contributions"""
        profile = CapabilityProfile()
        profile.update_from_contribution("code_optimization", 90)
        stars = profile.stars("python")
        assert stars >= 2  # High quality → noticeable improvement

    def test_multiple_contributions_grow_rating(self):
        """Multiple contributions in same domain increase rating"""
        profile = CapabilityProfile()
        for _ in range(10):
            profile.update_from_contribution("code_creation", 85)
        assert profile.stars("python") >= 3

    def test_low_quality_less_improvement(self):
        """Low quality contributions give minimal improvement"""
        profile = CapabilityProfile()
        profile.update_from_contribution("code_optimization", 30)
        stars = profile.stars("python")
        assert stars == 1  # Very low quality → minimal change

    def test_capability_ceiling(self):
        """Stars capped at 5"""
        profile = CapabilityProfile()
        for _ in range(100):
            profile.update_from_contribution("tool_development", 100)
        assert profile.stars("python") <= 5

    def test_unknown_contribution_type_ignored(self):
        """Unknown type doesn't change any rating"""
        profile = CapabilityProfile()
        before = profile.stars("python")
        profile.update_from_contribution("unknown_type", 90)
        assert profile.stars("python") == before

    def test_to_dict_format(self):
        profile = CapabilityProfile()
        profile.update_from_contribution("code_optimization", 95)
        d = profile.to_dict()
        assert "python" in d
        assert "stars" in d["python"]
        assert "rating" in d["python"]
        assert 1 <= d["python"]["stars"] <= 5

    def test_summary_top_capabilities(self):
        profile = CapabilityProfile()
        profile.update_from_contribution("code_optimization", 95)
        profile.update_from_contribution("code_creation", 90)
        profile.update_from_contribution("knowledge_organization", 88)

        summary = profile.summary()
        assert len(summary) <= 3
        assert "python" in summary  # Code tasks → python domain


# ============================================================
# Soulbound Tests
# ============================================================

class TestSoulbound:
    def test_identity_is_always_soulbound(self):
        """Agent identity is always soulbound"""
        with tempfile.TemporaryDirectory() as tmpdir:
            node_ident = NodeIdentity.create(node_name="Soulbound", data_dir=tmpdir)
            agent = AgentIdentity.create(node_ident, 0)
            assert agent.soulbound == True
            # Cannot be set to False during normal operations
            # (This is enforced by design, not by setter)

    def test_identity_bound_to_node(self):
        """Agent identity cannot be detached from its node"""
        with tempfile.TemporaryDirectory() as tmpdir:
            node_ident = NodeIdentity.create(node_name="Bound", data_dir=tmpdir)
            agent = AgentIdentity.create(node_ident, 5, name="bound-test")
            assert agent.owner_node_id == node_ident.node_id
            assert agent.owner_public_key_hex == node_ident.public_key_hex
            assert AgentIdentity.verify_ownership(
                agent.agent_id,
                node_ident.public_key_hex,
                agent.creation_index,
            )
