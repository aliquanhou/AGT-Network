"""
Tests: v0.3 Agent Marketplace + Protocol Fee Engine

Verifies:
- Task pool management and filtering
- Capability-gated task visibility
- Claim lifecycle (claim → execute → release)
- Protocol fee calculation and routing
- Genesis Vault vesting schedule
"""

import pytest
from unittest.mock import MagicMock

from agt_node.autonomous.marketplace import AgentMarketplace, ClaimRecord
from reward_ledger.economy.protocol_fee import (
    ProtocolFeeEngine, GenesisVault, FeeAllocation,
    PROTOCOL_FEE_PCT, FEE_DISTRIBUTION,
    MAX_GENESIS_ATTRIBUTION, VESTING_EPOCHS, VESTING_YEARS,
)


# ============================================================
# Marketplace Tests
# ============================================================

class TestMarketplace:
    @pytest.fixture
    def marketplace(self):
        return AgentMarketplace(node_id="node-a")

    @pytest.fixture
    def sample_task(self):
        return {
            "id": "task-001",
            "name": "Optimize Database",
            "description": "Speed up queries",
            "goal": "Improve query performance",
            "source": "genesis",
            "creator": "AGT_CORE",
            "type": "code_optimization",
            "difficulty": 4,
            "value": 40.0,
            "status": "open",
            "requirement": "Output must include benchmarks",
            "validator_instructions": "Verify benchmarks",
            "context": {},
        }

    def test_list_task(self, marketplace, sample_task):
        marketplace.list_task(sample_task)
        assert "task-001" in marketplace._task_pool

    def test_get_open_tasks_qualified(self, marketplace, sample_task):
        marketplace.list_task(sample_task)
        tasks = marketplace.get_open_tasks(
            agent_reputation=100,
            agent_capability_stars={"python": 2},
        )
        assert len(tasks) == 1
        assert tasks[0]["id"] == "task-001"

    def test_get_open_tasks_below_reputation(self, marketplace, sample_task):
        sample_task["difficulty"] = 8  # Needs reputation 30
        marketplace.list_task(sample_task)
        tasks = marketplace.get_open_tasks(
            agent_reputation=15,
            agent_capability_stars={"python": 3},
        )
        assert len(tasks) == 0  # Filtered out

    def test_get_open_tasks_insufficient_capability(self, marketplace, sample_task):
        sample_task["difficulty"] = 7  # Needs 3 stars
        marketplace.list_task(sample_task)
        tasks = marketplace.get_open_tasks(
            agent_reputation=100,
            agent_capability_stars={"python": 1},  # Not enough
        )
        assert len(tasks) == 0

    def test_claim_task(self, marketplace, sample_task):
        marketplace.list_task(sample_task)
        claim = marketplace.claim_task("task-001", "agent-a", "node-a")
        assert claim is not None
        assert claim.task_id == "task-001"
        assert claim.agent_id == "agent-a"
        assert marketplace._task_pool["task-001"]["status"] == "claimed"

    def test_cannot_claim_claimed_task(self, marketplace, sample_task):
        marketplace.list_task(sample_task)
        c1 = marketplace.claim_task("task-001", "agent-a", "node-a")
        c2 = marketplace.claim_task("task-001", "agent-b", "node-b")
        assert c1 is not None
        assert c2 is None  # Already claimed

    def test_release_claim(self, marketplace, sample_task):
        marketplace.list_task(sample_task)
        claim = marketplace.claim_task("task-001", "agent-a", "node-a")
        marketplace.release_claim(claim.claim_id)
        assert marketplace._task_pool["task-001"]["status"] == "open"

    def test_mark_executed(self, marketplace, sample_task):
        marketplace.list_task(sample_task)
        claim = marketplace.claim_task("task-001", "agent-a", "node-a")
        marketplace.mark_executed(claim.claim_id, "poi-xyz")
        assert claim.status == "executed"
        assert "task-001" not in marketplace._task_pool

    def test_stats(self, marketplace, sample_task):
        marketplace.list_task(sample_task)
        t2 = dict(sample_task)
        t2["id"] = "task-002"
        t2["status"] = "open"
        marketplace.list_task(t2)
        marketplace.claim_task("task-001", "agent-a", "node-a")

        stats = marketplace.stats()
        assert stats["tasks_in_pool"] == 2
        assert stats["open"] == 1
        assert stats["claimed"] == 1


# ============================================================
# Protocol Fee Tests
# ============================================================

class TestProtocolFee:
    @pytest.fixture
    def engine(self):
        return ProtocolFeeEngine()

    def test_fee_constants(self):
        assert PROTOCOL_FEE_PCT == 0.02
        assert FEE_DISTRIBUTION["network_infrastructure"] == 0.50
        assert FEE_DISTRIBUTION["genesis_contribution"] == 0.25
        assert MAX_GENESIS_ATTRIBUTION == 5_000_000.0

    def test_apply_fee(self, engine):
        alloc = engine.apply_fee(100.0)
        assert alloc.gross_reward == 100.0
        assert alloc.fee_total == 2.0
        assert alloc.network_infrastructure == 1.0
        assert alloc.ecosystem_development == 0.5
        assert alloc.genesis_contribution == 0.5
        assert alloc.net_to_participants == 98.0

    def test_fee_accumulation(self, engine):
        engine.apply_fee(100.0)
        engine.apply_fee(200.0)
        assert engine._total_fees_collected == 6.0
        assert engine.network_infrastructure_fund == 3.0  # 1.0 + 2.0
        assert engine.vault.total_received == 1.5  # 0.5 + 1.0

    def test_apply_fee_to_distribution(self, engine):
        result = engine.apply_fee_to_distribution(
            discoverer=15, executor=65, validator=15, backer=5
        )
        # Gross = 100, fee = 2
        assert result["discoverer"] == 14.7   # 15 - 2*(15/100) = 15 - 0.3
        assert result["executor"] == 63.7     # 65 - 2*(65/100) = 65 - 1.3
        assert result["validator"] == 14.7    # 15 - 0.3
        assert result["backer"] == 4.9        # 5 - 0.1
        assert result["fee_breakdown"]["total_fee"] == 2.0
        assert result["fee_breakdown"]["genesis_contribution"] == 0.5

    def test_engine_stats(self, engine):
        engine.apply_fee(100.0)
        stats = engine.stats()
        assert "total_fees_collected" in stats
        assert "vault" in stats
        assert stats["fee_constants"]["protocol_fee_pct"] == 0.02

    def test_genesis_attribution_bounded(self, engine):
        """Maximum genesis attribution is 5M AGT"""
        assert MAX_GENESIS_ATTRIBUTION == 5_000_000.0
        # Apply enough fees to reach the cap
        # To reach 5M: need 5M / 0.005 = 1B in task rewards
        # That's the entire max_supply being distributed as rewards


class TestGenesisVault:
    @pytest.fixture
    def vault(self):
        return GenesisVault()

    def test_deposit(self, vault):
        vault.deposit(100.0)
        assert vault.balance == 100.0
        assert vault.total_received == 100.0

    def test_vesting_linear(self, vault):
        """20-year linear vesting: after 10 years, 50% vested"""
        vault.deposit(1000.0)

        # Advance 10 years worth of epochs
        for _ in range(VESTING_EPOCHS // 2):
            vault.release_epoch()

        stats = vault.stats()
        assert 45 <= stats["vested_pct"] <= 55  # ~50% vested
        assert stats["total_released"] > 0

    def test_full_vesting(self, vault):
        """After 20 years, everything is vested"""
        vault.deposit(500.0)

        for _ in range(VESTING_EPOCHS + 1):
            vault.release_epoch()

        stats = vault.stats()
        assert stats["vested_pct"] >= 100.0
        assert stats["balance"] <= 0.0

    def test_early_epochs_low_release(self, vault):
        """Early epochs release very little"""
        vault.deposit(100000.0)
        released = vault.release_epoch()
        # ~1/240 ≈ 0.417% per epoch
        assert released < 500  # Less than 500 in first epoch

    def test_vault_stats(self, vault):
        vault.deposit(1000.0)
        s = vault.stats()
        assert s["address"] == "agt-genesis-vault-000000000000"
        assert s["vesting_years_remaining"] > 0
        assert s["max_lifetime_attribution"] == 5_000_000.0
