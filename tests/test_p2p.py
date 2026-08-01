"""
Tests: P2P Network Layer — Discovery + Connection (v0.1)

验证:
- 节点发现（UDP 多播）
- WebSocket 连接
- 消息收发
- 节点离线检测
"""

import asyncio
import pytest

from p2p_network.protocol import (
    AGTMessage,
    MessageType,
    announce_payload,
    task_broadcast_payload,
)
from p2p_network.discovery import Discovery, PeerInfo
from p2p_network.connection import ConnectionManager


# ============================================================
# Protocol Tests
# ============================================================

class TestProtocol:
    def test_message_serialization(self):
        """消息序列化/反序列化"""
        msg = AGTMessage(
            type=MessageType.NODE_ANNOUNCE,
            node_id="test-node-1",
            payload={"host": "127.0.0.1", "port": 8001},
        )
        raw = msg.to_json()
        restored = AGTMessage.from_json(raw)

        assert restored.type == msg.type
        assert restored.node_id == msg.node_id
        assert restored.msg_id == msg.msg_id
        assert restored.payload == msg.payload

    def test_all_message_types(self):
        """所有消息类型可序列化"""
        for msg_type in MessageType:
            msg = AGTMessage(type=msg_type, node_id="test")
            raw = msg.to_json()
            restored = AGTMessage.from_json(raw)
            assert restored.type == msg_type

    def test_create_response(self):
        """创建响应消息"""
        req = AGTMessage(
            type=MessageType.NODE_QUERY,
            node_id="node-a",
        )
        resp = req.create_response(
            MessageType.NODE_RESPONSE,
            {"peers": []},
        )
        assert resp.type == MessageType.NODE_RESPONSE
        assert resp.node_id == req.node_id

    def test_payload_helpers(self):
        """Payload 构建辅助函数"""
        announce = announce_payload("127.0.0.1", 8001, "test-node")
        assert announce["host"] == "127.0.0.1"
        assert announce["port"] == 8001

        task = task_broadcast_payload({"id": "task-1", "name": "test"})
        assert task["task"]["id"] == "task-1"


# ============================================================
# Discovery Tests
# ============================================================

class TestDiscovery:
    @pytest.mark.asyncio
    async def test_discovery_create(self):
        """Discovery 实例创建"""
        disco = Discovery(node_id="test-node", port=8001)
        assert disco.node_id == "test-node"
        assert disco.port == 8001
        assert disco.peer_count == 0

    def test_peer_info(self):
        """PeerInfo 属性"""
        peer = PeerInfo(node_id="peer-1", host="10.0.0.1", port=8002)
        assert peer.ws_url == "ws://10.0.0.1:8002/ws"
        assert peer.is_active

    @pytest.mark.asyncio
    async def test_discovery_start_stop(self):
        """Discovery 启动和停止"""
        disco = Discovery(node_id="test-node", port=8001)
        task = asyncio.create_task(disco.start())
        await asyncio.sleep(1)
        await disco.stop()
        # 等待任务完成
        try:
            await asyncio.wait_for(task, timeout=2)
        except asyncio.TimeoutError:
            task.cancel()

    @pytest.mark.asyncio
    async def test_discovery_ignores_own_broadcast(self):
        """Discovery 忽略自身广播"""
        peers_found = []

        def on_peer(peer):
            peers_found.append(peer.node_id)

        disco = Discovery(node_id="node-a", port=8001)
        disco.on_peer_discovered(on_peer)

        # Simulate receiving own announce
        own_data = (
            b'{"type":"NODE_ANNOUNCE","node_id":"node-a","host":"127.0.0.1","port":8001}'
        )
        await disco._handle_message(own_data, ("127.0.0.1", 9999))
        assert len(peers_found) == 0


# ============================================================
# Connection Tests
# ============================================================

class TestConnection:
    @pytest.mark.asyncio
    async def test_connection_create(self):
        """ConnectionManager 实例创建"""
        mgr = ConnectionManager(node_id="test-node", port=8001)
        assert mgr.node_id == "test-node"
        assert mgr.port == 8001

    @pytest.mark.asyncio
    async def test_server_start_stop(self):
        """WebSocket 服务器启动和停止"""
        mgr = ConnectionManager(node_id="test-server", port=18761)
        await mgr.start()
        assert mgr._running

        # 验证服务器在监听
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", 18761))
        sock.close()
        assert result == 0  # 端口开放

        await mgr.stop()
        assert not mgr._running


class TestP2PIntegration:
    """双节点集成测试"""

    @pytest.mark.asyncio
    async def test_two_nodes_connect(self):
        """两个节点建立 WebSocket 连接"""
        # 启动节点 B 的服务器
        mgr_b = ConnectionManager(node_id="node-b", port=18762)
        await mgr_b.start()

        received_msgs = []

        async def on_message(peer_id, msg):
            received_msgs.append((peer_id, msg.type))

        mgr_b.on_message(on_message)

        # 节点 A 连接到节点 B
        mgr_a = ConnectionManager(node_id="node-a", port=18763)
        await mgr_a.start()
        await mgr_a.connect_to_peer("node-b", "127.0.0.1", 18762)

        await asyncio.sleep(0.5)

        # 发送消息
        msg = AGTMessage(
            type=MessageType.NODE_ANNOUNCE,
            node_id="node-a",
            payload={"host": "127.0.0.1", "port": 18763},
        )
        await mgr_a.send_to_peer("node-b", msg)

        await asyncio.sleep(0.5)

        assert len(received_msgs) > 0
        assert received_msgs[0][0] == "node-a"

        await mgr_a.stop()
        await mgr_b.stop()
