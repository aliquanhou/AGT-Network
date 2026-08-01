"""
AGT Network — Real-World Task: Knowledge Base Builder

This example demonstrates an AGT Agent building a structured knowledge entry
from research materials — a task with real utility for documentation teams.

The agent:
1. Receives research materials (papers, articles, notes)
2. Organizes and synthesizes the information
3. Produces a structured knowledge entry in markdown
4. The output is directly usable as documentation

Real-world use case: technical documentation, research synthesis, knowledge management.
"""

import asyncio


RESEARCH_MATERIALS = """
Proof of Intelligence (PoI) is a proposed consensus mechanism for AI agent networks.
Unlike Proof of Work (PoW) which validates computational effort through hash puzzles,
PoI validates intellectual effort through verified task completion.

Key differences:
- PoW: work → hash → reward. PoI: task → execution → validation → proof → reward
- PoW rewards energy expenditure. PoI rewards value creation.
- PoW is objective (hash is either correct or not). PoI requires subjective evaluation.

The Intelligence Proof is the core data structure. It contains:
1. Task metadata (what was done)
2. Execution output (the actual work)
3. Evidence chain (proof of the work's authenticity)
4. Validator assessment (independent quality evaluation)
5. Cryptographic signature (Ed25519, non-repudiable)

Impact measurement distinguishes PoI from simple completion rewards:
A contribution's value = completion quality × downstream usage × verification × time decay.
"""

KNOWLEDGE_TASK = {
    "id": "real-knowledge-001",
    "name": "Knowledge Entry: Proof of Intelligence Deep Dive",
    "description": (
        "Create a comprehensive knowledge base entry about Proof of Intelligence. "
        "Synthesize the provided research materials into a well-structured, "
        "reader-friendly document suitable for technical audiences."
    ),
    "goal": (
        "Produce a markdown document covering: (1) What is PoI, "
        "(2) How it compares to PoW and PoS, (3) Technical architecture, "
        "(4) Intelligence Proof data structure, (5) Impact measurement, "
        "(6) Use cases and future directions."
    ),
    "source": "human_request",
    "creator": "research-team",
    "type": "knowledge_organization",
    "difficulty": 4,
    "value": 40.0,
    "requirement": (
        "Output must be in well-formatted markdown with: "
        "table of contents, clear section headings, comparison tables, "
        "diagrams (ASCII art), and reference links."
    ),
    "context": {
        "materials": RESEARCH_MATERIALS,
        "audience": "technical",
        "format": "markdown",
    },
}


async def run_knowledge_example(node_url: str = "http://localhost:8001"):
    """Run the knowledge organization task through an AGT Node."""
    from sdk.client import AGTClient

    client = AGTClient(node_url)
    if not client.health():
        print("⚠ AGT Node not reachable. Start with: python main.py --port 8001")
        return

    print("=" * 60)
    print("  AGT Real-World Task: Knowledge Base Builder")
    print("=" * 60)
    print(f"  Task: {KNOWLEDGE_TASK['name']}")
    print(f"  Difficulty: {KNOWLEDGE_TASK['difficulty']}/10")
    print(f"  Value: {KNOWLEDGE_TASK['value']} AGT Credit")
    print()
    print("  [INFO] Genesis tasks include similar knowledge organization tasks.")
    print("  [INFO] Start node and run a cycle to see this in action:")
    print("        python main.py --port 8001 --run-cycle")
    print()


if __name__ == "__main__":
    asyncio.run(run_knowledge_example())
