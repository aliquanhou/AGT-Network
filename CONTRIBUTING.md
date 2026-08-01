# Contributing to AGT Network

Thank you for your interest in contributing to the AGT Network protocol.

## Ways to Contribute

### Run a Node
The most valuable contribution is running an AGT Node with real LLM backends and contributing to the Intelligence Ledger.

```bash
git clone https://github.com/your-org/AGT-Network.git
cd AGT-Network
pip install -r requirements.txt cryptography
cp .env.example .env  # Add your LLM API key
python main.py --port 8001
```

### Report Issues
Found a bug? Have a protocol design concern? Open an issue with:
- AGT version (`python main.py --version`)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs

### Submit Code
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`python -m pytest tests/`)
5. Submit a pull request

### Protocol Design
AGT is a protocol, not just a codebase. Design discussions happen through:
- Issues tagged `protocol-design`
- The [Decision Log](genesis-archive/DECISION_LOG.md) for precedent

## Development Setup

```bash
# Clone
git clone https://github.com/your-org/AGT-Network.git
cd AGT-Network

# Install
pip install -r requirements.txt cryptography

# Test
python -m pytest tests/ -v

# Run single node
python main.py --port 8001

# Run dual node simulation
python main.py --dual

# Run E2E verification
python main.py --test
```

## Code Style

- Python 3.11+
- Type hints on public APIs
- Dataclasses for data structures
- Tests in `tests/` mirroring module structure
- All tests must pass before PR merge

## Architecture Principles

1. **Protocol first, implementation second** — the data structures are the spec
2. **Test before trust** — cryptographic verification beats heuristic trust
3. **Immutable by default** — LedgerBlock seals after creation
4. **Soulbound reputation** — earned, not purchased or transferred
5. **Supply-guarded rewards** — can't exceed protocol-defined max

## Questions?

Open a discussion or issue. AGT is an open protocol — your questions improve it.
