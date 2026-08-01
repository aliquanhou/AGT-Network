"""
AGT SDK — Examples

Ready-to-run examples for common AGT SDK operations.

Usage:
    python -m sdk.examples
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.client import AGTClient


def example_status():
    """Example: Check node status"""
    client = AGTClient("http://localhost:8001")
    node = client.status()
    print(f"  Node: {node.node_name} ({node.node_id})")
    print(f"  Peers: {node.peers} | Agents: {node.agents}")
    print(f"  Tasks completed: {node.tasks_completed}")
    print(f"  Total credit: {node.total_credit:.1f} AGT")


def example_list_tasks():
    """Example: List available tasks"""
    client = AGTClient("http://localhost:8001")
    tasks = client.list_tasks()
    print(f"  Open tasks: {len(tasks)}")
    for t in tasks[:5]:
        print(f"  - [{t.task_type}] {t.name} (diff={t.difficulty}, value={t.value})")


def example_list_contributions():
    """Example: View recent contributions"""
    client = AGTClient("http://localhost:8001")
    contribs = client.list_contributions(limit=10)
    print(f"  Recent contributions: {len(contribs)}")
    for c in contribs[:5]:
        print(f"  - {c['task_name']}: score={c['contribution_score']:.1f}, "
              f"+{c['agt_credit']:.1f} AGT Credit")


def example_verify_chain():
    """Example: Verify ledger integrity"""
    client = AGTClient("http://localhost:8001")
    result = client.verify_chain()
    if result["valid"]:
        print(f"  Chain integrity VERIFIED — {result['blocks']} blocks")
    else:
        print(f"  Chain BROKEN: {result['message']}")


def example_reputation():
    """Example: View reputation leaderboard"""
    client = AGTClient("http://localhost:8001")
    reps = client.reputation_leaderboard()
    print(f"  Reputation leaderboard:")
    for i, r in enumerate(reps[:5]):
        print(f"  #{i+1}: {r['agent_id']} — {r['score']:.0f} ({r['level']}, {r['reward_multiplier']}x)")


def run_all():
    """Run all examples"""
    print("AGT SDK — Examples\n")

    for name, fn in [
        ("1. Node Status", example_status),
        ("2. Open Tasks", example_list_tasks),
        ("3. Recent Contributions", example_list_contributions),
        ("4. Chain Verification", example_verify_chain),
        ("5. Reputation Leaderboard", example_reputation),
    ]:
        print(f"--- {name} ---")
        try:
            fn()
        except Exception as e:
            print(f"  Error: {e}")
        print()


if __name__ == "__main__":
    run_all()
