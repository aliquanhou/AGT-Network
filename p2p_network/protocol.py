"""
AGT P2P Protocol — v0.1 Message Definitions

消息类型: NODE_ANNOUNCE / TASK_BROADCAST / TASK_RESULT /
          CONTRIBUTION_BROADCAST / NODE_QUERY

v0.1: JSON over UDP (discovery) + WebSocket (direct communication)
v0.5: libp2p
v1.0: AGT P2P Protocol
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
import json
import time
import uuid


class MessageType(str, Enum):
    """AGT P2P 消息类型"""
    NODE_ANNOUNCE = "NODE_ANNOUNCE"
    NODE_QUERY = "NODE_QUERY"
    NODE_RESPONSE = "NODE_RESPONSE"
    TASK_BROADCAST = "TASK_BROADCAST"
    TASK_CLAIM = "TASK_CLAIM"
    TASK_RESULT = "TASK_RESULT"
    CONTRIBUTION_BROADCAST = "CONTRIBUTION_BROADCAST"
    VALIDATOR_REQUEST = "VALIDATOR_REQUEST"
    VALIDATOR_RESPONSE = "VALIDATOR_RESPONSE"


@dataclass
class AGTMessage:
    """Base AGT network message"""
    type: MessageType
    node_id: str
    timestamp: float = field(default_factory=time.time)
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: dict = field(default_factory=dict)

    def to_json(self) -> str:
        data = {
            "type": self.type.value,
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "msg_id": self.msg_id,
            "payload": self.payload,
        }
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "AGTMessage":
        data = json.loads(raw)
        return cls(
            type=MessageType(data["type"]),
            node_id=data["node_id"],
            timestamp=data.get("timestamp", time.time()),
            msg_id=data.get("msg_id", str(uuid.uuid4())),
            payload=data.get("payload", {}),
        )

    def create_response(self, resp_type: MessageType, payload: dict = None) -> "AGTMessage":
        """Create a response message to this message"""
        return AGTMessage(
            type=resp_type,
            node_id=self.node_id,
            payload=payload or {},
        )


# ============================================================
# Payload helpers
# ============================================================

def announce_payload(host: str, port: int, node_name: str = "") -> dict:
    """Build NODE_ANNOUNCE payload"""
    return {
        "host": host,
        "port": port,
        "node_name": node_name,
    }


def task_broadcast_payload(task: dict) -> dict:
    """Build TASK_BROADCAST payload"""
    return {"task": task}


def task_result_payload(task_id: str, result: dict, agent_id: str) -> dict:
    """Build TASK_RESULT payload"""
    return {
        "task_id": task_id,
        "result": result,
        "agent_id": agent_id,
    }


def contribution_payload(proof: dict) -> dict:
    """Build CONTRIBUTION_BROADCAST payload"""
    return {"proof": proof}
