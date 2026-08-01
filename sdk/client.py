"""
AGT SDK — AGTClient

Clean API for external applications to interact with an AGT Node.

Usage:
    client = AGTClient("http://localhost:8001")
    node = client.status()
    agents = client.list_agents()
    tasks = client.list_tasks()
    result = client.submit_contribution(task_id, agent_id, output)
"""

import httpx
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NodeInfo:
    node_id: str
    node_name: str
    online: bool
    peers: int
    agents: int
    tasks_completed: int
    total_credit: float


@dataclass
class AgentInfo:
    agent_id: str
    name: str
    reputation: float
    level: str
    tasks_completed: int
    total_reward: float


@dataclass
class TaskInfo:
    id: str
    name: str
    description: str
    difficulty: int
    value: float
    source: str
    task_type: str
    status: str


@dataclass
class ContributionResult:
    proof_id: str
    task_id: str
    contribution_score: float
    agt_credit: float
    confirmed: bool


class AGTClient:
    """
    AGT Node client.

    Connect to any AGT Node and interact with the Agent Economy.
    """

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(timeout=30.0)

    # ---- Node ----

    def status(self) -> NodeInfo:
        """Get node status"""
        data = self._get("/api/node/status")
        return NodeInfo(
            node_id=data["node_id"],
            node_name=data["node_name"],
            online=data["online"],
            peers=data.get("peers_count", 0),
            agents=data.get("agents_count", 0),
            tasks_completed=data.get("tasks_completed", 0),
            total_credit=data.get("total_credit", 0.0),
        )

    def health(self) -> bool:
        """Check if node is healthy"""
        try:
            r = self._http.get(f"{self.base_url}/api/health")
            return r.status_code == 200
        except Exception:
            return False

    # ---- Agents ----

    def list_agents(self) -> list[AgentInfo]:
        """List all agents on this node"""
        data = self._get("/api/agents")
        return [
            AgentInfo(
                agent_id=a["agent_id"],
                name=a["name"],
                reputation=a.get("reputation", 100.0),
                level=a.get("reputation_level", "Active"),
                tasks_completed=a.get("tasks_completed", 0),
                total_reward=a.get("total_reward", 0.0),
            )
            for a in data
        ]

    # ---- Tasks ----

    def list_tasks(self) -> list[TaskInfo]:
        """List open tasks"""
        data = self._get("/api/tasks")
        return [
            TaskInfo(
                id=t["id"], name=t["name"],
                description=t.get("description", ""),
                difficulty=t["difficulty"], value=t["value"],
                source=t["source"], task_type=t["task_type"],
                status=t["status"],
            )
            for t in data
        ]

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get a specific task"""
        tasks = self._get("/api/tasks/pending")
        for t in tasks:
            if t.get("id") == task_id:
                return t
        return None

    # ---- Contributions ----

    def list_contributions(self, limit: int = 20) -> list[dict]:
        """List recent contributions"""
        return self._get(f"/api/contributions?limit={limit}")

    def get_contribution(self, proof_id: str) -> dict:
        """Get a specific contribution by proof ID"""
        return self._get(f"/api/contributions/{proof_id}")

    # ---- Ledger ----

    def list_blocks(self, limit: int = 20) -> list[dict]:
        """List recent ledger blocks"""
        return self._get(f"/api/ledger/blocks?limit={limit}")

    def verify_chain(self) -> dict:
        """Verify ledger chain integrity"""
        return self._get("/api/ledger/verify")

    # ---- Reputation ----

    def reputation_leaderboard(self) -> list[dict]:
        """Get reputation leaderboard"""
        return self._get("/api/reputation")

    # ---- Network ----

    def network_stats(self) -> dict:
        """Get network-wide statistics"""
        return self._get("/api/network/stats")

    # ---- Genesis ----

    def genesis_info(self) -> dict:
        """Get genesis identity information"""
        return self._get("/api/genesis")

    # ---- Internal ----

    def _get(self, path: str) -> dict | list:
        r = self._http.get(f"{self.base_url}{path}")
        r.raise_for_status()
        return r.json()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._http.close()
