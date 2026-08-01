FROM python:3.12-slim

LABEL org.agt-network.version="v0.36.2"
LABEL org.agt-network.description="AGT Network — Open Agent Intelligence Economy Protocol"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt cryptography

# App code
COPY . .

# Data volume
VOLUME ["/app/data"]

# Dashboard + API
EXPOSE 8001
# P2P WebSocket
EXPOSE 9001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

ENV AGT_HOST=0.0.0.0
ENV AGT_PORT=8001
ENV AGT_NODE_NAME="AGT Node"

CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8001", "--p2p-port", "9001"]
