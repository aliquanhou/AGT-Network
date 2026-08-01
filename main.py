#!/usr/bin/env python3
"""
AGT Network v0.1 — Genesis Prototype

Entry point for AGT Node.

Usage:
    # Start a node with API + Dashboard
    python main.py --port 8001 --node-name "AGT Node A"

    # Start a node and run one economic cycle
    python main.py --port 8001 --run-cycle

    # Run automated end-to-end test
    python main.py --test

    # Start two nodes (simulated network)
    python main.py --dual
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def get_args():
    parser = argparse.ArgumentParser(
        description="AGT Network v0.1 — Genesis Prototype",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --port 8001 --node-name "AGT Node A"
  python main.py --port 8002 --node-name "AGT Node B"
  python main.py --test
  python main.py --dual
        """,
    )
    parser.add_argument("--port", type=int, default=8001, help="HTTP API + Dashboard port (default: 8001)")
    parser.add_argument("--p2p-port", type=int, default=None, help="P2P WebSocket port (default: port + 1000)")
    parser.add_argument("--node-name", default="AGT Node", help="Node display name")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--llm-provider", default=None, help="LLM provider: deepseek|openai|claude|ollama")
    parser.add_argument("--llm-api-key", default=None, help="LLM API key")
    parser.add_argument("--llm-model", default=None, help="LLM model name")
    parser.add_argument("--run-cycle", action="store_true", help="Run one economic cycle then exit")
    parser.add_argument("--test", action="store_true", help="Run automated end-to-end test")
    parser.add_argument("--dual", action="store_true", help="Start two nodes on ports 8001+8002")
    parser.add_argument("--data-dir", default="./data", help="Data directory (default: ./data)")
    parser.add_argument("--continuous", action="store_true", help="Continuously process tasks")
    return parser.parse_args()


async def run_single_node(args):
    """Run a single AGT Node"""
    from agt_node.node import AGTNode

    node = AGTNode(
        node_name=args.node_name,
        port=args.port,
        p2p_port=args.p2p_port,
        host=args.host,
        llm_provider=args.llm_provider,
        llm_api_key=args.llm_api_key,
        llm_model=args.llm_model,
        data_dir=args.data_dir,
    )

    await node.start()
    node.api_server.set_node(node)

    # Start API in background
    api_task = asyncio.create_task(node.api_server.start())
    print(f"\n  AGT Dashboard: http://{args.host}:{args.port}")
    print(f"  P2P Network:   ws://{args.host}:{node.p2p_port}\n")

    if args.run_cycle:
        await node.run_economy_loop(continuous=False)
        # Clean shutdown: cancel API server, then stop node
        api_task.cancel()
        try:
            await api_task
        except asyncio.CancelledError:
            pass
        await node.stop()
    elif args.continuous:
        print("  Continuous economy loop active. Press Ctrl+C to stop.")
        await node.run_economy_loop(continuous=True)
    else:
        # Wait for API to be accessed, then run one cycle on demand
        print("  Node running. Access the Dashboard or press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("\n  Shutting down...")
        finally:
            await node.stop()


async def run_dual_nodes(args):
    """Start two AGT Nodes for local testing"""
    from agt_node.node import AGTNode

    print("\n  === AGT Network — Dual Node Mode ===\n")

    # Node A
    node_a = AGTNode(
        node_name="AGT Node A",
        port=8001,
        p2p_port=9001,
        host="127.0.0.1",
        llm_provider=args.llm_provider,
        llm_api_key=args.llm_api_key,
        llm_model=args.llm_model,
        data_dir="./data/node-a",
    )

    # Node B
    node_b = AGTNode(
        node_name="AGT Node B",
        port=8002,
        p2p_port=9002,
        host="127.0.0.1",
        llm_provider=args.llm_provider,
        llm_api_key=args.llm_api_key,
        llm_model=args.llm_model,
        data_dir="./data/node-b",
    )

    await node_a.start()
    await node_b.start()

    # Connect nodes to each other via P2P ports
    await node_a.connection.connect_to_peer(node_b.node_id, "127.0.0.1", 9002)

    # Start API servers
    asyncio.create_task(node_a.api_server.start())
    asyncio.create_task(node_b.api_server.start())

    print(f"\n  Dashboard A: http://127.0.0.1:8001")
    print(f"  Dashboard B: http://127.0.0.1:8002\n")

    # Run one cycle on Node A
    print("  --- Running economy cycle on Node A ---")
    result_a = await node_a.run_task_cycle()

    # Run one cycle on Node B
    print("  --- Running economy cycle on Node B ---")
    result_b = await node_b.run_task_cycle()

    print("\n  === Dual Node Test Complete ===")
    print(f"  Node A: +{result_a.get('reward_credit', 0)} AGT Credit")
    print(f"  Node B: +{result_b.get('reward_credit', 0)} AGT Credit")

    # Keep running for dashboard access
    print("\n  Nodes running. Access Dashboards or press Ctrl+C to stop.")
    try:
        await asyncio.sleep(600)
    except KeyboardInterrupt:
        pass
    finally:
        await node_a.stop()
        await node_b.stop()


async def run_e2e_test(args):
    """Run automated end-to-end verification test"""
    print("\n  === AGT Genesis Prototype — End-to-End Verification ===\n")

    from agt_node.node import AGTNode

    node = AGTNode(
        node_name="AGT Test Node",
        port=args.port,
        p2p_port=args.p2p_port,
        host="127.0.0.1",
        llm_provider=args.llm_provider,
        llm_api_key=args.llm_api_key,
        llm_model=args.llm_model,
        data_dir="./data/test",
    )

    await node.start()

    # Create an agent
    agent = node.create_agent(name="Test Agent")
    print(f"  [1] Agent created: {agent.agent_id}")

    # Run economic cycle
    print(f"  [2] Running economic cycle...")
    result = await node.run_task_cycle()

    checks = []

    # Check 1: Task was executed
    checks.append(("Task executed", "error" not in result))
    print(f"  [3] Task execution: {'OK' if checks[-1][1] else 'FAIL'}")

    # Check 2: Contribution verified
    confirmed = result.get("confirmed", False)
    checks.append(("Contribution verified", confirmed))
    print(f"  [4] Contribution verified: {'OK' if confirmed else 'FAIL'}")

    # Check 3: Reward issued
    reward = result.get("reward_credit", 0)
    checks.append(("Reward issued", reward > 0))
    print(f"  [5] Reward issued: {'OK (+{:.1f} AGT Credit)'.format(reward) if reward > 0 else 'FAIL'}")

    # Check 4: Intelligence Proof generated
    proof_id = result.get("proof_id", "")
    checks.append(("PoI generated", bool(proof_id)))
    print(f"  [6] Intelligence Proof: {'OK ({})'.format(proof_id) if proof_id else 'FAIL'}")

    # Check 5: Reputation updated
    if node.agents:
        rep = node.reputations.get(list(node.agents.keys())[0])
        rep_changed = rep.score != 100 if rep else False
        checks.append(("Reputation updated", rep_changed))
        print(f"  [7] Reputation: {rep.score:.0f} {'OK' if rep_changed else 'NOTE: unchanged'}")

    # Check 6: Ledger recorded
    ledger_blocks = node.ledger.total_contributions
    checks.append(("Ledger recorded", ledger_blocks > 1))
    print(f"  [8] Ledger: {ledger_blocks} blocks {'OK' if ledger_blocks > 1 else 'FAIL'}")

    # Check 7: Wallet credited
    if node.wallets:
        wallet = list(node.wallets.values())[0]
        checks.append(("Wallet credited", wallet.balance > 0))
        print(f"  [9] Wallet: {wallet.balance:.1f} AGT Credit {'OK' if wallet.balance > 0 else 'FAIL'}")

    # Check 8: Chain integrity
    chain_ok = node.ledger.verify_chain()
    checks.append(("Chain integrity", chain_ok))
    print(f"  [10] Chain integrity: {'OK' if chain_ok else 'BROKEN!'}")

    # Summary
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"\n  === Results: {passed}/{total} checks passed ===\n")

    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    print()

    if passed == total:
        print("  *** AGT Genesis Prototype -- ALL CHECKS PASSED ***")
        print("  The first Agent Economy experimental loop is complete!")
    else:
        print(f"  ⚠ {total - passed} check(s) failed")

    await node.stop()
    return passed == total


def main():
    args = get_args()

    if args.test:
        success = asyncio.run(run_e2e_test(args))
        sys.exit(0 if success else 1)
    elif args.dual:
        try:
            asyncio.run(run_dual_nodes(args))
        except KeyboardInterrupt:
            pass
    else:
        try:
            asyncio.run(run_single_node(args))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
