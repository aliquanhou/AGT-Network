"""
AGT API Server — FastAPI routes

Exposes REST + WebSocket endpoints for the AGT Dashboard.
Provides CRUD access to: Node / Agent / Task / Contribution / Ledger / Reputation
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================================
# Pydantic Models (API schemas)
# ============================================================

class NodeStatusOut(BaseModel):
    node_id: str
    node_name: str
    online: bool = True
    peers_count: int = 0
    agents_count: int = 0
    tasks_completed: int = 0
    total_credit: float = 0.0
    reputation: float = 100.0
    last_heartbeat: str = ""  # v0.36.4: ISO timestamp of last activity


class AgentOut(BaseModel):
    agent_id: str
    name: str
    node_id: str
    tasks_completed: int = 0
    total_reward: float = 0.0
    reputation: float = 100.0
    reputation_level: str = "Active"


class TaskOut(BaseModel):
    id: str
    name: str
    description: str
    difficulty: int
    value: float
    source: str
    creator: str
    task_type: str
    status: str


class ContributionOut(BaseModel):
    proof_id: str
    task_id: str
    task_name: str
    agent_id: str
    node_id: str
    contribution_type: str
    contribution_score: float
    agt_credit: float
    evidence_count: int
    validator_node_id: str
    created_at: str


class LedgerBlockOut(BaseModel):
    block_id: str
    index: int
    node_id: str
    agent_id: str
    task_id: str
    reward_credit: float
    reputation_change: float
    block_hash: str
    timestamp: str


class NetworkStatsOut(BaseModel):
    total_nodes: int
    total_agents: int
    total_tasks: int
    total_contributions: int
    total_credit_issued: float
    network_uptime: str


# ============================================================
# App
# ============================================================

class AGTAPIServer:
    """
    FastAPI server wrapping the AGT node's internal state.

    Provides REST endpoints for the Dashboard and
    WebSocket for real-time updates.
    """

    def __init__(self, node: "AGTNode" = None, port: int = 8001):
        self.node = node
        self.port = port
        self.app = FastAPI(title="AGT Network API", version="v0.1-genesis")
        self._ws_clients: list[WebSocket] = []
        self._started_at = datetime.now(timezone.utc)
        self._setup_routes()
        self._setup_websocket()

    def set_node(self, node: "AGTNode"):
        """Inject the AGT Node reference after construction"""
        self.node = node

    # ---- Route Setup ----

    def _setup_routes(self):
        app = self.app

        # Dashboard static files
        dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "web_dashboard")
        if os.path.isdir(dashboard_dir):
            app.mount("/static", StaticFiles(directory=dashboard_dir), name="dashboard_static")

        @app.get("/")
        async def dashboard():
            dashboard_html = os.path.join(os.path.dirname(__file__), "..", "web_dashboard", "index.html")
            if os.path.isfile(dashboard_html):
                return FileResponse(dashboard_html)
            return {"message": "AGT Network API", "dashboard": "web_dashboard/index.html not found"}

        @app.get("/api/health")
        async def health():
            return {"status": "ok", "network": "AGT Network v0.1-genesis"}

        # ---- Node ----

        @app.get("/api/node/status")
        async def node_status():
            if not self.node:
                return NodeStatusOut(
                    node_id="not-initialized",
                    node_name="AGT Node",
                    online=True,
                )
            # v0.36.4: update heartbeat on status check
            from datetime import datetime, timezone
            self.node._last_heartbeat = datetime.now(timezone.utc).isoformat()
            return NodeStatusOut(
                node_id=self.node.node_id,
                node_name=self.node.node_name,
                online=True,
                peers_count=self.node.connection.peer_count if self.node.connection else 0,
                agents_count=len(self.node.agents),
                tasks_completed=self.node.ledger.total_contributions if self.node.ledger else 0,
                total_credit=self.node.ledger.total_credit_issued if self.node.ledger else 0.0,
                reputation=(
                    self.node.reputations.get(
                        list(self.node.agents.keys())[0]
                    ).score
                    if self.node.agents and self.node.reputations
                    else 100.0
                ),
                last_heartbeat=self.node._last_heartbeat or "",
            )

        @app.get("/api/node/heartbeat")
        async def node_heartbeat():
            """v0.36.4: Heartbeat endpoint for node health monitoring"""
            from datetime import datetime, timezone
            if self.node:
                self.node._last_heartbeat = datetime.now(timezone.utc).isoformat()
                return {"status": "ok", "last_heartbeat": self.node._last_heartbeat}
            return {"status": "no_node"}

        # ---- Agents ----

        @app.get("/api/agents")
        async def list_agents():
            if not self.node:
                return []
            agents = []
            for aid, agent in self.node.agents.items():
                rep = self.node.reputations.get(aid)
                agents.append(AgentOut(
                    agent_id=aid,
                    name=agent.name,
                    node_id=agent.owner_node_id,
                    tasks_completed=agent.tasks_completed,
                    total_reward=agent.total_reward,
                    reputation=rep.score if rep else 100.0,
                    reputation_level=rep.level if rep else "Active",
                ))
            return agents

        # ---- Tasks ----

        @app.get("/api/tasks")
        async def list_tasks():
            if not self.node:
                return []
            tasks = self.node.dispatcher.get_open_tasks() if self.node.dispatcher else []
            return [
                TaskOut(
                    id=t["id"], name=t["name"], description=t["description"],
                    difficulty=t["difficulty"], value=t["value"],
                    source=t["source"], creator=t["creator"],
                    task_type=t["type"], status=t["status"],
                )
                for t in tasks
            ]

        @app.get("/api/tasks/pending")
        async def pending_tasks():
            if not self.node or not self.node.dispatcher:
                return []
            return [t.to_dict() for t in self.node.dispatcher.get_pending_tasks()]

        # ---- Contributions ----

        @app.get("/api/contributions")
        async def list_contributions(limit: int = 20):
            if not self.node or not self.node.consensus:
                return []
            # Read from ledger blocks
            if not self.node.ledger:
                return []
            blocks = self.node.ledger.get_latest_blocks(limit)
            contributions = []
            for b in blocks:
                if b.contribution_proof and b.index > 0:  # Skip genesis
                    proof = b.contribution_proof
                    contributions.append(ContributionOut(
                        proof_id=proof.proof_id,
                        task_id=proof.task_id,
                        task_name=proof.task_name,
                        agent_id=proof.agent_id,
                        node_id=proof.node_id,
                        contribution_type=proof.contribution_type.value,
                        contribution_score=proof.contribution_score,
                        agt_credit=proof.agt_credit,
                        evidence_count=len(proof.evidence),
                        validator_node_id=proof.validator_node_id,
                        created_at=proof.created_at,
                    ))
            return contributions

        @app.get("/api/contributions/{proof_id}")
        async def get_contribution(proof_id: str):
            if not self.node or not self.node.ledger:
                return {"error": "Not available"}
            for b in self.node.ledger.blocks:
                if b.contribution_proof and b.contribution_proof.proof_id == proof_id:
                    return b.contribution_proof.to_dict()
            return {"error": "Proof not found"}

        # ---- Ledger ----

        @app.get("/api/ledger/blocks")
        async def list_blocks(limit: int = 20):
            if not self.node or not self.node.ledger:
                return []
            return [
                LedgerBlockOut(
                    block_id=b.block_id,
                    index=b.index,
                    node_id=b.node_id,
                    agent_id=b.agent_id,
                    task_id=b.task_id,
                    reward_credit=b.reward_credit,
                    reputation_change=b.reputation_change,
                    block_hash=b.block_hash,
                    timestamp=b.timestamp,
                )
                for b in self.node.ledger.get_latest_blocks(limit)
            ]

        @app.get("/api/ledger/verify")
        async def verify_chain():
            if not self.node or not self.node.ledger:
                return {"valid": False, "message": "No ledger"}
            valid = self.node.ledger.verify_chain()
            return {
                "valid": valid,
                "blocks": len(self.node.ledger.blocks),
                "message": "Chain integrity OK" if valid else "Chain BROKEN!",
            }

        # ---- Reputation ----

        @app.get("/api/reputation")
        async def reputation_leaderboard():
            if not self.node or not self.node.reputations:
                return []
            leaderboard = []
            for aid, rep in self.node.reputations.items():
                leaderboard.append({
                    "agent_id": aid,
                    "score": rep.score,
                    "level": rep.level,
                    "reward_multiplier": rep.reward_multiplier,
                })
            leaderboard.sort(key=lambda x: x["score"], reverse=True)
            return leaderboard

        # ---- Network Stats ----

        @app.get("/api/network/stats")
        async def network_stats():
            if not self.node:
                return NetworkStatsOut(
                    total_nodes=0, total_agents=0, total_tasks=0,
                    total_contributions=0, total_credit_issued=0.0,
                    network_uptime="0s",
                )
            uptime = datetime.now(timezone.utc) - self._started_at
            return NetworkStatsOut(
                total_nodes=1 + (self.node.connection.peer_count if self.node.connection else 0),
                total_agents=len(self.node.agents),
                total_tasks=sum(1 for t in self.node.dispatcher._pending_tasks if t.status == "open") if self.node.dispatcher else 0,
                total_contributions=self.node.ledger.total_contributions if self.node.ledger else 0,
                total_credit_issued=self.node.ledger.total_credit_issued if self.node.ledger else 0.0,
                network_uptime=str(uptime).split(".")[0],
            )

        # ---- Genesis Identity ----

        @app.get("/api/genesis")
        async def genesis_info():
            if not self.node or not self.node.genesis_identity:
                return {"message": "Genesis identity not yet created"}
            return self.node.genesis_identity.to_dict()

    def _setup_websocket(self):
        app = self.app

        @app.websocket("/ws")
        async def ws_endpoint(ws: WebSocket):
            await ws.accept()
            self._ws_clients.append(ws)
            try:
                while True:
                    # Keep alive + wait for events
                    await ws.receive_text()
            except WebSocketDisconnect:
                self._ws_clients.remove(ws)
            except asyncio.CancelledError:
                # Server shutting down — clean exit
                pass
            except Exception:
                if ws in self._ws_clients:
                    self._ws_clients.remove(ws)

    async def broadcast_event(self, event_type: str, data: dict):
        """Push real-time event to all Dashboard clients"""
        import json
        msg = json.dumps({"type": event_type, "data": data})
        disconnected = []
        for ws in self._ws_clients:
            try:
                await ws.send_text(msg)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            if ws in self._ws_clients:
                self._ws_clients.remove(ws)

    # ---- Startup ----

    async def start(self):
        """Start the API server"""
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        logger.info(f"[API] Starting AGT API Server on port {self.port}")
        await server.serve()

    def run(self):
        """Synchronous entry point"""
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")
