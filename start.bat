@echo off
title AGT Network Node
echo.
echo  ⚡ AGT Network v0.35 — Genesis Testnet
echo  ======================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python 3.11+ required. Install from https://python.org
    pause
    exit /b 1
)

REM Check deps
python -c "import websockets, fastapi, httpx" >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Installing dependencies...
    python -m pip install -r requirements.txt cryptography -q
)

REM Copy env if needed
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo  [INFO] Created .env from .env.example — add your LLM API key!
        echo  [INFO] Edit .env and restart.
        pause
        exit /b 0
    )
)

echo  [INFO] Starting AGT Node...
echo  [INFO] Dashboard: http://localhost:8001
echo  [INFO] Press Ctrl+C to stop.
echo.
python main.py --port 8001 --host 0.0.0.0

pause
