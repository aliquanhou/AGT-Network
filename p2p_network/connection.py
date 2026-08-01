"""
AGT P2P Connection — WebSocket node direct connection management

Manages WebSocket connections between nodes.
Each node is both a WebSocket server (receiving connections)
and a client (connecting to other nodes).

Usage:
    conn_mgr = ConnectionManager(node_id="node-a", port=8001)
    await conn_mgr.start()
    await conn_mgr.send_to_peer("node-b", msg)
"""

import asyncio
import json
import logging
from typing import Callable, Optional

import websockets
from websockets.asyncio.server import ServerConnection
from websockets.asyncio.client import ClientConnection

from .protocol import AGTMessage, MessageType

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager.

    Responsibilities:
    - Start WebSocket server
    - Actively connect to discovered nodes
    - Manage multiple WebSocket connections
    - Message routing
    """

    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 8001):
        self.node_id = node_id
        self.host = host
        self.port = port

        self._server = None
        self._running = False
        self._connections: dict[str, ClientConnection | ServerConnection] = {}
        self._message_handler: Optional[Callable] = None

    # ---- callbacks ----

    def on_message(self, handler: Callable):
        """Register message handler: async def handler(peer_id: str, msg: AGTMessage)"""
        self._message_handler = handler

    @property
    def peer_count(self) -> int:
        return len(self._connections)

    async def start(self):
        """Start WebSocket server"""
        self._running = True
        self._server = await websockets.serve(
            self._handle_incoming,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10,
        )
        logger.info(f"[Connection] WebSocket server started ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop all connections"""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for peer_id, ws in list(self._connections.items()):
            try:
                await ws.close()
            except Exception:
                pass
        self._connections.clear()
        logger.info("[Connection] All connections closed")

    # ---- peer connections ----

    async def connect_to_peer(self, peer_id: str, host: str, port: int):
        """Actively connect to another node"""
        if peer_id == self.node_id:
            return
        if peer_id in self._connections:
            return

        url = f"ws://{host}:{port}/ws"
        try:
            ws = await websockets.connect(url, ping_interval=20, ping_timeout=10)
            # Send identity message immediately so the server recognizes us
            ident = AGTMessage(
                type=MessageType.NODE_ANNOUNCE,
                node_id=self.node_id,
                payload={"host": self.host, "port": self.port},
            )
            await ws.send(ident.to_json())

            self._connections[peer_id] = ws
            logger.info(f"[Connection] Connected to node {peer_id} @ {url}")

            # Start receive loop
            asyncio.create_task(self._receive_loop(peer_id, ws))
        except Exception as e:
            logger.warning(f"[Connection] Failed to connect {peer_id}: {e}")

    async def disconnect_peer(self, peer_id: str):
        """Disconnect from a peer"""
        ws = self._connections.pop(peer_id, None)
        if ws:
            await ws.close()

    async def send_to_peer(self, peer_id: str, msg: AGTMessage):
        """Send message to a specific peer"""
        ws = self._connections.get(peer_id)
        if ws:
            try:
                await ws.send(msg.to_json())
            except Exception as e:
                logger.warning(f"[Connection] Send to {peer_id} failed: {e}")
                await self.disconnect_peer(peer_id)
        else:
            logger.warning(f"[Connection] Not connected to {peer_id}")

    async def broadcast(self, msg: AGTMessage, exclude: Optional[list[str]] = None):
        """Broadcast message to all connected peers"""
        exclude = exclude or []
        for peer_id in list(self._connections.keys()):
            if peer_id not in exclude:
                await self.send_to_peer(peer_id, msg)

    # ---- internals ----

    async def _handle_incoming(self, ws: ServerConnection):
        """Handle incoming WebSocket connection"""
        peer_id = None
        try:
            # Wait for the identity message from connecting client
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
            msg = AGTMessage.from_json(raw)
            peer_id = msg.node_id

            if peer_id == self.node_id:
                await ws.close(1008, "Self-connection rejected")
                return

            # Close old connection if exists
            old_ws = self._connections.pop(peer_id, None)
            if old_ws:
                await old_ws.close()

            self._connections[peer_id] = ws
            logger.info(f"[Connection] Node {peer_id} connected to ws://{self.host}:{self.port}")

            # Enter receive loop
            await self._receive_loop(peer_id, ws)

        except asyncio.TimeoutError:
            logger.warning("[Connection] Connection timeout: no identity message received")
            await ws.close()
        except Exception as e:
            logger.warning(f"[Connection] Connection handling error: {e}")
        finally:
            if peer_id:
                self._connections.pop(peer_id, None)
                logger.info(f"[Connection] Node {peer_id} disconnected")

    async def _receive_loop(self, peer_id: str, ws):
        """Receive message loop"""
        try:
            async for raw in ws:
                try:
                    msg = AGTMessage.from_json(raw)
                    if self._message_handler:
                        await self._message_handler(peer_id, msg)
                except json.JSONDecodeError:
                    logger.warning(f"[Connection] Invalid JSON received: {raw[:100]}")
                except Exception as e:
                    logger.warning(f"[Connection] Message handling error: {e}")
        except websockets.ConnectionClosed:
            logger.info(f"[Connection] {peer_id} connection closed")
        finally:
            self._connections.pop(peer_id, None)
