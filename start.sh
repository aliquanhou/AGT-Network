#!/usr/bin/env bash
set -e

echo ""
echo " ⚡ AGT Network v0.35 — Genesis Testnet"
echo " ======================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo " [ERROR] Python 3.11+ required. Install from https://python.org"
    exit 1
fi

# Install deps
python3 -c "import websockets, fastapi, httpx" 2>/dev/null || {
    echo " [INFO] Installing dependencies..."
    python3 -m pip install -r requirements.txt cryptography -q
}

# Copy env if needed
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo " [INFO] Created .env from .env.example — add your LLM API key!"
        echo " [INFO] Edit .env and restart."
        exit 0
    fi
fi

echo " [INFO] Starting AGT Node..."
echo " [INFO] Dashboard: http://localhost:8001"
echo " [INFO] Press Ctrl+C to stop."
echo ""

python3 main.py --port 8001 --host 0.0.0.0
