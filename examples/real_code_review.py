"""
AGT Network — Real-World Task: Open Source Code Review

This example demonstrates an AGT Agent performing a real code review task.

The agent:
1. Receives a code sample from an open-source project
2. Analyzes code quality, security, and performance
3. Produces a structured review report with recommendations
4. The output can be used as a real GitHub PR review

This is a REAL task — not a simulated benchmark.
"""

import asyncio
from pathlib import Path


SAMPLE_CODE = '''
def process_orders(orders):
    """Process a list of customer orders."""
    results = []
    for order in orders:
        # Validate order
        if order["quantity"] <= 0:
            continue
        if order["price"] <= 0:
            continue

        # Calculate total
        total = order["quantity"] * order["price"]

        # Apply discount
        if total > 100:
            total = total * 0.9
        elif total > 50:
            total = total * 0.95

        # Check inventory (simulated)
        if order.get("item_id") is None:
            continue

        # Add to results
        results.append({
            "order_id": order.get("id"),
            "customer": order.get("customer", "unknown"),
            "total": round(total, 2),
            "status": "processed"
        })

    return results
'''

CODE_REVIEW_TASK = {
    "id": "real-code-review-001",
    "name": "Code Review: process_orders Function",
    "description": (
        "Review the provided order processing function for: "
        "(1) performance bottlenecks, (2) error handling gaps, "
        "(3) code clarity and maintainability, (4) potential bugs. "
        "Provide a structured review with specific recommendations."
    ),
    "goal": (
        "Produce a professional code review report covering performance, "
        "error handling, code clarity, and potential bugs. Include specific "
        "line references and actionable improvement suggestions."
    ),
    "source": "human_request",
    "creator": "open-source-maintainer",
    "type": "code_optimization",
    "difficulty": 3,
    "value": 30.0,
    "requirement": (
        "Output must include: (1) Summary of findings, "
        "(2) Performance analysis, (3) Error handling review, "
        "(4) Code clarity assessment, (5) Specific fix recommendations "
        "with code snippets."
    ),
    "context": {
        "code_sample": SAMPLE_CODE,
        "language": "python",
        "project": "open-source-ecommerce",
    },
}


async def run_code_review_example(node_url: str = "http://localhost:8001"):
    """
    Run the code review task through an AGT Node.

    Prerequisites:
    1. AGT Node running: python main.py --port 8001
    2. LLM API key configured in .env
    """
    from sdk.client import AGTClient

    client = AGTClient(node_url)

    # Check node is running
    if not client.health():
        print("⚠ AGT Node not reachable. Start with: python main.py --port 8001")
        return

    print("=" * 60)
    print("  AGT Real-World Task: Open Source Code Review")
    print("=" * 60)
    print()
    print(f"  Task: {CODE_REVIEW_TASK['name']}")
    print(f"  Difficulty: {CODE_REVIEW_TASK['difficulty']}/10")
    print(f"  Value: {CODE_REVIEW_TASK['value']} AGT Credit")
    print()
    print("  Code to review:")
    print(f"  {SAMPLE_CODE.strip()[:200]}...")
    print()
    print("  [INFO] This task would be submitted to the AGT Node.")
    print("  [INFO] An Agent would execute the code review using LLM.")
    print("  [INFO] A Validator would evaluate the review quality.")
    print("  [INFO] The contribution would be recorded in the Intelligence Ledger.")
    print()
    print("  To run this example with a live node:")
    print("  1. Start node: python main.py --port 8001 --run-cycle")
    print("  2. The Genesis tasks include similar code review tasks")
    print()
    print("  For now, review the task definition at:")
    print("  examples/real_code_review.py")
    print()


if __name__ == "__main__":
    asyncio.run(run_code_review_example())
