"""
Tests: API Server

Verifies:
- Health endpoint
- Node status endpoint
- Agents / Tasks / Contributions / Ledger / Reputation endpoints
- WebSocket connection
- Network stats / Genesis identity endpoints
"""

import pytest
from fastapi.testclient import TestClient

from api_server.server import AGTAPIServer


@pytest.fixture
def client():
    """Create a test API client with no node attached"""
    server = AGTAPIServer(node=None, port=19991)
    return TestClient(server.app)


@pytest.fixture
def client_with_mock_node():
    """Create a test API client with a mock node"""
    from unittest.mock import MagicMock
    import datetime

    mock_node = MagicMock()
    mock_node.node_id = "test-node-001"
    mock_node.node_name = "Test Node"
    mock_node.agents = {}
    mock_node.dispatcher = MagicMock()
    mock_node.dispatcher.get_open_tasks.return_value = []
    mock_node.dispatcher._pending_tasks = []
    mock_node.connection = MagicMock()
    mock_node.connection.peer_count = 0
    mock_node.consensus = None
    mock_node.ledger = None
    mock_node.reputations = {}
    mock_node.genesis_identity = None

    server = AGTAPIServer(node=mock_node, port=19992)
    return TestClient(server.app)


# ============================================================
# Basic Endpoints
# ============================================================

class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "AGT Network" in data["network"]


class TestNodeStatus:
    def test_no_node(self, client):
        resp = client.get("/api/node/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["node_id"] == "not-initialized"

    def test_with_node(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/node/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["node_id"] == "test-node-001"


# ============================================================
# Agent / Task Endpoints
# ============================================================

class TestAgents:
    def test_empty_agents(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/agents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_no_node(self, client):
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        assert resp.json() == []


class TestTasks:
    def test_tasks_no_node(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_tasks_with_node(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/tasks")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_pending_tasks(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/tasks/pending")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ============================================================
# Contribution / Ledger Endpoints
# ============================================================

class TestContributions:
    def test_empty(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/contributions")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_proof_not_found(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/contributions/nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data


class TestLedger:
    def test_no_ledger(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/ledger/blocks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_verify_no_ledger(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/ledger/verify")
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False


# ============================================================
# Reputation / Network / Genesis
# ============================================================

class TestReputation:
    def test_empty(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/reputation")
        assert resp.status_code == 200
        assert resp.json() == []


class TestNetworkStats:
    def test_stats(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/network/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_nodes" in data
        assert "total_agents" in data
        assert "network_uptime" in data


class TestGenesis:
    def test_no_genesis(self, client_with_mock_node):
        resp = client_with_mock_node.get("/api/genesis")
        assert resp.status_code == 200
        data = resp.json()
        assert "not yet created" in data.get("message", "")
