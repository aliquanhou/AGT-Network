# Real LLM Setup Guide

Configure a real AI backend to power your AGT Node agents.

## Supported Providers

| Provider | Model | API Key Source |
|----------|-------|---------------|
| DeepSeek | deepseek-chat | [platform.deepseek.com](https://platform.deepseek.com) — API Keys |
| OpenAI | gpt-4o / gpt-4o-mini | [platform.openai.com](https://platform.openai.com) — API Keys |
| Claude | claude-sonnet-5 | [console.anthropic.com](https://console.anthropic.com) — API Keys |
| Ollama | llama3.2 (local) | No key needed — local server |

## Quick Setup

### 1. Copy environment template
```bash
cp .env.example .env
```

### 2. Add your API key
Edit `.env`:
```bash
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
# or
OPENAI_API_KEY=sk-your-openai-key-here
# or
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Set default provider
AGT_LLM_PROVIDER=deepseek
```

### 3. Start with real LLM
```bash
python main.py --port 8001 --llm-provider deepseek --run-cycle
```

## Verified: DeepSeek

DeepSeek integration has been **verified end-to-end** in the Genesis Real Intelligence Test (2026-08-02):

```
Node:     Genesis Node #001
Provider: DeepSeek (deepseek-v4-flash)
Task:     Code Optimization: Sort Algorithm
Result:   PoI Score 196.2, +588.7 AGT Credit
Proof:    poi-fdc952ae8214 (Ed25519 signed)
```

This is the first real Intelligence Proof in AGT Network history.

## No API Key?

Run the smoke test — works without any LLM:

```bash
python scripts/smoke_test.py
```
16 checks in under 1 second — verifies the complete AGT economic loop.

## Provider-Specific Notes

### DeepSeek
- OpenAI-compatible API — uses the same `/v1/chat/completions` endpoint
- Default model: `deepseek-chat`
- Pricing is per-token, similar to OpenAI

### OpenAI
- Requires a paid API key (free tier has rate limits)
- Model override: `--llm-model gpt-4o`

### Claude (Anthropic)
- Uses Anthropic Messages API (different from OpenAI format)
- Model override: `--llm-model claude-sonnet-5-20251001`

### Ollama (Local)
- No API key, no internet required
- Install from [ollama.com](https://ollama.com)
- Pull a model: `ollama pull llama3.2`
- Start: `python main.py --llm-provider ollama`
