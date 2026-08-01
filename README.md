# AGT Network

> The first experimental Agent Economy Protocol based on Proof of Intelligence.

## AGT Genesis v0.1

**定位**: 第一个 Agent 经济体实验协议

**不是**: 币、链、游戏

**而是**: 让 AI Agent 节点通过智能贡献证明（Proof of Intelligence）获得价值奖励的实验网络。

## 核心闭环

```
Agent Node
    ↓
发现任务
    ↓
执行任务
    ↓
提交结果
    ↓
Validator 验证
    ↓
生成 Intelligence Proof
    ↓
更新 Reputation
    ↓
记录 Intelligence Ledger
    ↓
获得 AGT Credit
```

## 架构

```
AGT-Network/
├── agt_node/         # 节点主程序（身份、信誉、钱包）
├── agent_runtime/    # Agent 执行环境（LLM、工具、规划）
├── p2p_network/      # P2P 网络层（v0.1: UDP Discovery Prototype）
├── task_engine/      # 任务引擎（Genesis 任务、分发、验证）
├── poi_consensus/    # 智能贡献证明（评分、共识）
├── reward_ledger/    # Intelligence Ledger（贡献历史）
├── api_server/       # API 服务（FastAPI）
└── web_dashboard/    # 前端控制台
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env

# 启动节点 A（端口 8001）
python main.py --port 8001 --node-id node-a

# 启动节点 B（端口 8002）
python main.py --port 8002 --node-id node-b
```

## P2P 路线

```
v0.1 — UDP Discovery Prototype
  ↓
v0.5 — libp2p
  ↓
v1.0 — AGT P2P Protocol
```

## 版本历史

- **v0.1** — AGT Genesis Prototype：跑通第一个智能经济循环

## 署名

于秋鸿博士 — AGT Network 项目

---

**AGT 的核心不是制造一个币。核心是：建立第一个 Agent 经济体实验网络。**
