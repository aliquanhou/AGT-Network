# AGT Network — Real-World Task Examples

This directory contains ready-to-run examples of AGT Agents performing
real tasks with genuine utility — not simulated benchmarks.

## Examples

| File | Task Type | Real-World Use Case |
|------|-----------|---------------------|
| `real_code_review.py` | Code Optimization | GitHub PR code review |
| `real_knowledge_builder.py` | Knowledge Organization | Technical documentation synthesis |

## Usage

Each example can be run independently. They connect to a running AGT Node.

```bash
# Start the node first
python main.py --port 8001

# Then run an example
python examples/real_code_review.py
python examples/real_knowledge_builder.py
```

## What These Examples Prove

1. **Agents can perform real work** — not just simulated tasks
2. **Output is directly usable** — code reviews can be posted as GitHub comments;
   knowledge entries can be published as documentation
3. **Impact is measurable** — if a code review leads to a merged PR,
   the Impact Oracle records it. If a knowledge entry is cited by other documents,
   the Impact Oracle records it.
4. **The economic loop closes** — real work → verified contribution → recorded proof → earned credit

## Adding Your Own Tasks

See the [tutorial](TUTORIAL.md) for a step-by-step guide to creating custom tasks.

## Genesis Tasks

The 4 built-in Genesis tasks (`genesis-001` through `genesis-004`) are also
real-world tasks covering code optimization, knowledge organization,
creative design, and tool development.

```bash
# View all genesis tasks via the API
curl http://localhost:8001/api/tasks
```
