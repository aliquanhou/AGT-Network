"""
AGT P2P Discovery — v0.1 UDP Discovery Prototype

基于 UDP 多播的局域网节点发现机制。
所有节点加入同一个多播组，周期性广播自身信息，
同时监听其他节点的广播。

v0.1: UDP Multicast (局域网测试)
v0.5: libp2p (跨网络)
v1.0: AGT P2P Protocol (全球)

Usage:
    disco = Discovery(node_id="node-a", port=8001)
    await disco.start()
    peers = disco.get_peers()
"""

import asyncio
import json
import logging
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ============================================================
# Constants
# ============================================================
MULTICAST_GROUP = "239.255.0.1"  # 本地管理多播地址
MULTICAST_PORT = 9999
ANNOUNCE_INTERVAL = 5.0  # 每 5 秒广播一次
PEER_TIMEOUT = 30.0  # 30 秒未收到心跳视为离线


@dataclass
class PeerInfo:
    """已知节点信息"""
    node_id: str
    host: str
    port: int
    node_name: str = ""
    last_seen: float = field(default_factory=time.time)
    is_active: bool = True

    @property
    def ws_url(self) -> str:
        return f"ws://{self.host}:{self.port}/ws"


class Discovery:
    """
    UDP 多播节点发现 (v0.1 Discovery Prototype)

    职责:
    - 周期性广播自身节点信息
    - 监听其他节点的广播
    - 维护已知节点列表
    - 检测离线节点
    """

    def __init__(
        self,
        node_id: str,
        port: int,
        host: str = "127.0.0.1",
        node_name: str = "",
        multicast_group: str = MULTICAST_GROUP,
        multicast_port: int = MULTICAST_PORT,
        announce_interval: float = ANNOUNCE_INTERVAL,
        peer_timeout: float = PEER_TIMEOUT,
    ):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.node_name = node_name or node_id
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.announce_interval = announce_interval
        self.peer_timeout = peer_timeout

        self._peers: dict[str, PeerInfo] = {}
        self._running = False
        self._on_peer_discovered: Optional[Callable] = None
        self._on_peer_lost: Optional[Callable] = None

    # ---- callbacks ----

    def on_peer_discovered(self, callback: Callable):
        """注册节点发现回调"""
        self._on_peer_discovered = callback

    def on_peer_lost(self, callback: Callable):
        """注册节点离线回调"""
        self._on_peer_lost = callback

    # ---- lifecycle ----

    async def start(self):
        """启动发现服务"""
        self._running = True
        logger.info(
            f"[Discovery v0.1] 启动 — Node {self.node_id} "
            f"({self.host}:{self.port}) 多播组 {self.multicast_group}:{self.multicast_port}"
        )
        await asyncio.gather(
            self._announce_loop(),
            self._listen_loop(),
            self._cleanup_loop(),
        )

    async def stop(self):
        """停止发现服务"""
        self._running = False
        logger.info(f"[Discovery] 停止 — Node {self.node_id}")

    # ---- peer access ----

    def get_peers(self) -> list[PeerInfo]:
        """获取所有活跃节点"""
        return [p for p in self._peers.values() if p.is_active]

    def get_peer(self, node_id: str) -> Optional[PeerInfo]:
        """根据 node_id 获取节点"""
        return self._peers.get(node_id)

    @property
    def peer_count(self) -> int:
        return len(self.get_peers())

    # ---- internals ----

    def _build_announce(self) -> dict:
        return {
            "type": "NODE_ANNOUNCE",
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "node_name": self.node_name,
            "timestamp": time.time(),
        }

    async def _announce_loop(self):
        """周期性广播"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        # Bind to local address for sending
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                data = json.dumps(self._build_announce()).encode("utf-8")
                await loop.run_in_executor(
                    None,
                    lambda: sock.sendto(data, (self.multicast_group, self.multicast_port)),
                )
                logger.debug(f"[Discovery] 广播发送 → {self.node_id}")
            except Exception as e:
                logger.warning(f"[Discovery] 广播失败: {e}")

            await asyncio.sleep(self.announce_interval)

        sock.close()

    async def _listen_loop(self):
        """监听其他节点广播"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.multicast_port))

        mreq = struct.pack("4sl", socket.inet_aton(self.multicast_group), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(0.5)

        loop = asyncio.get_event_loop()

        while self._running:
            try:
                data, addr = await loop.run_in_executor(
                    None,
                    sock.recvfrom,
                    4096,
                )
                await self._handle_message(data, addr)
            except socket.timeout:
                pass  # No data, continue
            except OSError:
                pass
            except Exception as e:
                if self._running:
                    logger.warning(f"[Discovery] Listen error: {e}")

        sock.close()

    async def _handle_message(self, data: bytes, addr: tuple):
        try:
            msg = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type")
        if msg_type != "NODE_ANNOUNCE":
            return

        peer_id = msg["node_id"]

        # 忽略自己的广播
        if peer_id == self.node_id:
            return

        now = time.time()
        if peer_id in self._peers:
            # 更新已知节点
            peer = self._peers[peer_id]
            peer.last_seen = now
            if not peer.is_active:
                peer.is_active = True
                logger.info(f"[Discovery] 节点恢复在线: {peer_id}")
                if self._on_peer_discovered:
                    self._on_peer_discovered(peer)
        else:
            # 新节点
            peer = PeerInfo(
                node_id=peer_id,
                host=msg.get("host", addr[0]),
                port=msg.get("port", 0),
                node_name=msg.get("node_name", peer_id),
                last_seen=now,
            )
            self._peers[peer_id] = peer
            logger.info(f"[Discovery] 发现新节点: {peer_id} @ {peer.host}:{peer.port}")
            if self._on_peer_discovered:
                self._on_peer_discovered(peer)

    async def _cleanup_loop(self):
        """清理超时节点"""
        while self._running:
            now = time.time()
            expired = []
            for node_id, peer in self._peers.items():
                if peer.is_active and (now - peer.last_seen) > self.peer_timeout:
                    peer.is_active = False
                    expired.append(node_id)
                    logger.info(f"[Discovery] 节点离线: {node_id}")
                    if self._on_peer_lost:
                        self._on_peer_lost(peer)

            # 可选：彻底删除过久的离线节点
            for node_id in expired:
                if (now - self._peers[node_id].last_seen) > self.peer_timeout * 3:
                    del self._peers[node_id]

            await asyncio.sleep(self.peer_timeout / 2)
