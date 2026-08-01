"""
AGT Node — Main Orchestrator

The AGTNode is the complete AGT network participant.
It integrates all subsystems into a single running process.

Architecture:
    AGTNode
    ├── identity (NodeIdentity + GenesisIdentity)
    ├── wallet (CreditWallet)
    ├── reputation (AgentReputation map)
    ├── p2p (Discovery + ConnectionManager)
    ├── agents (AgentRuntime map)
    ├── task engine (TaskDispatcher)
    ├── consensus (ConsensusEngine)
    ├── ledger (IntelligenceLedger)
    └── api (AGTAPIServer + Dashboard)

Full Economic Loop:
    Agent Node → Discover Task → Execute → Validate →
    Intelligence Proof → Reputation Update → Ledger Record → AGT Credit
"""

import asyncio
import logging
import sys
from pathlib import Path

from .identity import NodeIdentity, GenesisIdentity
from .reputation import AgentReputation, ReputationEvent
from .wallet import CreditWallet

from p2p_network.discovery import Discovery
from p2p_network.connection import ConnectionManager
from p2p_network.protocol import AGTMessage, MessageType, task_broadcast_payload, contribution_payload

from agent_runtime.llm_client import create_llm_client
from agent_runtime.agent import AGTAgent

from task_engine.tasks import get_genesis_tasks, AGTTask
from task_engine.dispatcher import TaskDispatcher
from task_engine.validator import Validator

from poi_consensus.consensus import ConsensusEngine
from poi_consensus.intelligence_proof import IntelligenceProof

from reward_ledger.ledger import IntelligenceLedger

from api_server.server import AGTAPIServer

logger = logging.getLogger(__name__)


class AGTNode:
    """
    AGT Network Node — complete Agent Economy participant.

    Usage:
        node = AGTNode(node_name="Node A", port=8001)
        await node.start()
        await node.run_economy_loop()
    """

    def __init__(
        self,
        node_name: str = "AGT Node",
        port: int = 8001,
        host: str = "127.0.0.1",
        llm_provider: str = None,
        llm_api_key: str = None,
        llm_model: str = None,
        founder_id: str = "",
        data_dir: str = "./data",
    ):
        # ---- Identity ----
        self.node_id = f"agt-node-{port}"
        self.node_name = node_name
        self.host = host
        self.port = port
        self.founder_id = founder_id or node_name

        # Genesis identity (historical record, not admin)
        self.genesis_identity = GenesisIdentity.create(
            founder_id=self.founder_id,
            node_id=self.node_id,
        )

        # ---- Subsystems ----
        self.discovery: Discovery = None
        self.connection: ConnectionManager = None
        self.agents: dict[str, AGTAgent] = {}
        self.wallets: dict[str, CreditWallet] = {}
        self.reputations: dict[str, AgentReputation] = {}
        self.dispatcher = TaskDispatcher()
        self.consensus = ConsensusEngine(node_id=self.node_id)
        self.ledger = IntelligenceLedger(data_dir=data_dir)
        self.api_server = AGTAPIServer(node=self, port=port)

        # ---- LLM ----
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.llm_client = None

        # ---- State ----
        self._running = False
        self._data_dir = data_dir
        Path(data_dir).mkdir(parents=True, exist_ok=True)

    # ============================================================
    # Lifecycle
    # ============================================================

    async def start(self):
        """Start the AGT Node and all subsystems"""
        logger.info(f"=" * 60)
        logger.info(f"AGT Node STARTING: {self.node_id}")
        logger.info(f"  Name: {self.node_name}")
        logger.info(f"  Founder: {self.founder_id}")
        logger.info(f"  Genesis Hash: {self.genesis_identity.genesis_hash[:16]}...")
        logger.info(f"=" * 60)

        self._running = True

        # 1. Load ledger
        self.ledger.load()
        if not self.ledger.blocks:
            self.ledger.create_genesis_block(self.founder_id)

        # 2. P2P Network
        self.discovery = Discovery(
            node_id=self.node_id,
            port=self.port,
            host=self.host,
            node_name=self.node_name,
        )
        self.discovery.on_peer_discovered(self._on_peer_discovered)
        self.discovery.on_peer_lost(self._on_peer_lost)

        self.connection = ConnectionManager(
            node_id=self.node_id,
            host=self.host,
            port=self.port,
        )
        self.connection.on_message(self._on_peer_message)
        await self.connection.start()

        # 3. LLM Client (if configured)
        if self.llm_provider and self.llm_api_key:
            try:
                self.llm_client = create_llm_client(
                    provider=self.llm_provider,
                    api_key=self.llm_api_key,
                    model=self.llm_model,
                )
                logger.info(f"[Node] LLM: {self.llm_provider} connected")
            except Exception as e:
                logger.warning(f"[Node] LLM not available: {e}")

        # 4. Load Genesis tasks into dispatcher
        self.dispatcher.add_tasks(get_genesis_tasks())
        logger.info(f"[Node] {len(get_genesis_tasks())} Genesis tasks loaded")

        # 5. Consensus callbacks — wire to ledger + reputation + wallet
        self.consensus.on_proof_generated(self._on_contribution_proof)
        self.consensus.on_reward(self._on_reward_issued)

        # 6. Connect API server's node reference
        self.api_server.set_node(self)

        # 7. Start discovery (background)
        asyncio.create_task(self.discovery.start())

        logger.info(f"[Node] AGT Node {self.node_id} STARTED on port {self.port}")

    async def stop(self):
        """Gracefully stop the node"""
        self._running = False
        try:
            if self.discovery:
                await self.discovery.stop()
            if self.connection:
                await self.connection.stop()
        except Exception:
            pass
        logger.info(f"[Node] AGT Node {self.node_id} STOPPED")

    # ============================================================
    # Agent Management
    # ============================================================

    def create_agent(self, agent_id: str = None, name: str = "") -> AGTAgent:
        """Register a new agent on this node"""
        if not agent_id:
            import uuid
            agent_id = f"agent-{uuid.uuid4().hex[:6]}"

        agent = AGTAgent(
            agent_id=agent_id,
            llm_client=self.llm_client,
            name=name or agent_id,
            owner_node_id=self.node_id,
        )
        self.agents[agent_id] = agent

        # Wallet for this agent
        wallet = CreditWallet(node_id=self.node_id, agent_id=agent_id)
        self.wallets[agent_id] = wallet

        # Reputation profile
        reputation = AgentReputation(agent_id=agent_id)
        self.reputations[agent_id] = reputation

        logger.info(f"[Node] Agent created: {agent_id} ({agent.name})")
        return agent

    # ============================================================
    # Task Lifecycle
    # ============================================================

    async def run_task_cycle(self, task_id: str = None) -> dict:
        """
        Execute one complete task cycle on this node.
        Picks a task, executes it, validates it, and records the contribution.

        Returns a summary dict of the cycle.
        """
        # 1. Pick a task
        if task_id:
            task = None
            for t in self.dispatcher._pending_tasks:
                if t.id == task_id and t.status == "open":
                    task = t
                    break
            if not task:
                return {"error": f"Task {task_id} not found or not open"}
        else:
            open_tasks = self.dispatcher.get_open_tasks()
            if not open_tasks:
                return {"error": "No open tasks available"}
            # Pick first open task
            task_id = open_tasks[0]["id"]
            task = None
            for t in self.dispatcher._pending_tasks:
                if t.id == task_id and t.status == "open":
                    task = t
                    break

        if not task:
            return {"error": "Could not find task"}

        # 2. Ensure we have an agent
        if not self.agents:
            self.create_agent()

        agent = list(self.agents.values())[0]
        agent_id = agent.agent_id

        logger.info(f"[Node] Starting task cycle: {task.id} → Agent {agent_id}")

        # 3. Execute task with Agent
        task_result = await agent.run_task(task.to_dict())

        # 4. Run consensus (validator on same node for v0.1 single-machine demo)
        consensus_result = await self.consensus.process_contribution(
            task=task,
            agent_id=agent_id,
            worker_node_id=self.node_id,
            result=task_result.execution.final_output,
            assignment_id=f"local-{task.id}",
        )

        # 5. Dispatch status update
        self.dispatcher.mark_submitted(f"local-{task.id}")
        if consensus_result.confirmed:
            self.dispatcher.mark_validated(f"local-{task.id}")
            self.dispatcher.mark_rewarded(f"local-{task.id}")

        return {
            "task_id": task.id,
            "task_name": task.name,
            "agent_id": agent_id,
            "execution_success": task_result.execution.success,
            "contribution_score": consensus_result.score.final_score,
            "confirmed": consensus_result.confirmed,
            "reward_credit": consensus_result.reward_credit,
            "proof_id": consensus_result.proof.proof_id,
        }

    # ============================================================
    # P2P Event Handlers
    # ============================================================

    async def _on_peer_discovered(self, peer):
        """When a new peer is discovered, connect via WebSocket"""
        logger.info(f"[Node] Peer discovered: {peer.node_id}")
        if self.connection:
            asyncio.create_task(
                self.connection.connect_to_peer(peer.node_id, peer.host, peer.port)
            )

    async def _on_peer_lost(self, peer):
        logger.info(f"[Node] Peer lost: {peer.node_id}")

    async def _on_peer_message(self, peer_id: str, msg: AGTMessage):
        """Handle incoming P2P messages"""
        if msg.type == MessageType.TASK_BROADCAST:
            # Another node published a task
            task_data = msg.payload.get("task", {})
            logger.info(f"[Node] Task broadcast received: {task_data.get('id')}")

        elif msg.type == MessageType.CONTRIBUTION_BROADCAST:
            proof_data = msg.payload.get("proof", {})
            logger.info(f"[Node] Contribution broadcast: {proof_data.get('proof_id')}")

        elif msg.type == MessageType.NODE_ANNOUNCE:
            # Peer info already handled by discovery
            pass

    # ============================================================
    # Economic Callbacks
    # ============================================================

    def _on_contribution_proof(self, proof: IntelligenceProof):
        """Called when consensus confirms a contribution"""
        agent_id = proof.agent_id

        # Update reputation
        rep = self.reputations.get(agent_id)
        if not rep:
            rep = AgentReputation(agent_id=agent_id)
            self.reputations[agent_id] = rep
        rep_delta = rep.apply_contribution_result(
            proof.contribution_score, proof.task_id
        )

        # Record in Intelligence Ledger (with supply guard)
        try:
            self.ledger.record_contribution(
                proof=proof,
                reputation_change=rep_delta,
                reward_credit=proof.agt_credit,
                node_id=self.node_id,
                agent_id=agent_id,
            )
        except ValueError as e:
            logger.warning(
                f"[Node] Contribution REJECTED by supply guard: {e}"
            )
            return  # Don't record — ledger rejected it

        logger.info(
            f"[Node] Contribution recorded: {proof.proof_id} "
            f"({proof.contribution_score:.1f} pts, {proof.agt_credit:.1f} AGT)"
        )

    def _on_reward_issued(self, agent_id: str, amount: float):
        """Called when AGT Credit is issued"""
        wallet = self.wallets.get(agent_id)
        if wallet:
            wallet.credit(amount, "consensus", "")
        else:
            wallet = CreditWallet(node_id=self.node_id, agent_id=agent_id)
            wallet.credit(amount, "consensus", "")
            self.wallets[agent_id] = wallet

        # Also credit to agent
        agent = self.agents.get(agent_id)
        if agent:
            agent.add_reward(amount)

    # ============================================================
    # Main Loop
    # ============================================================

    async def run_economy_loop(self, continuous: bool = False):
        """
        Run the AGT economy loop.

        If continuous=True, keeps processing tasks (v0.5+).
        If continuous=False, processes one cycle and reports (v0.1).
        """
        if continuous:
            while self._running:
                try:
                    result = await self.run_task_cycle()
                    if "error" in result:
                        logger.info(f"[Economy] No tasks available, waiting...")
                        await asyncio.sleep(10)
                    else:
                        logger.info(f"[Economy] Cycle complete: +{result['reward_credit']} AGT")
                        await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"[Economy] Cycle error: {e}")
                    await asyncio.sleep(10)
        else:
            # Single cycle
            result = await self.run_task_cycle()
            self._print_report(result)
            return result

    def _print_report(self, result: dict):
        """Print a summary report of the economy cycle"""
        if "error" in result:
            logger.warning(f"[Node] Cycle failed: {result['error']}")
            return

        print("\n" + "=" * 60)
        print("  AGT Genesis Prototype — Economic Cycle Report")
        print("=" * 60)
        print(f"  Task:       {result.get('task_name', 'N/A')}")
        print(f"  Agent:      {result.get('agent_id', 'N/A')}")
        print(f"  Score:      {result.get('contribution_score', 0):.1f}")
        print(f"  Confirmed:  {result.get('confirmed', False)}")
        print(f"  Reward:     +{result.get('reward_credit', 0):.1f} AGT Credit")
        print(f"  Proof ID:   {result.get('proof_id', 'N/A')}")
        print("=" * 60)

        # Print ledger status
        agent_id = result.get("agent_id")
        if agent_id:
            rep = self.reputations.get(agent_id)
            if rep:
                print(f"  Reputation: {rep.score:.0f} ({rep.level})")
            wallet = self.wallets.get(agent_id)
            if wallet:
                print(f"  Balance:    {wallet.balance:.1f} AGT Credit")
        print(f"  Ledger:     {self.ledger.total_contributions} blocks")
        print("=" * 60 + "\n")

    # ============================================================
    # Run
    # ============================================================

    def run(self, run_api: bool = True, run_economy: bool = True):
        """
        Synchronous entry point. Starts the node, optionally runs API + economy.
        """
        async def _run():
            await self.start()

            # Start API server in background
            if run_api:
                asyncio.create_task(self.api_server.start())
                logger.info(f"[Node] API Server: http://{self.host}:{self.port}")

            # Run economy loop
            if run_economy:
                await self.run_economy_loop(continuous=False)
            else:
                # Just stay alive
                while self._running:
                    await asyncio.sleep(60)

        asyncio.run(_run())
