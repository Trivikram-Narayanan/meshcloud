#!/bin/bash

# 1. Detect LAN IP Address (works on Mac and Linux)
IP=$(python3 -c 'import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); print(s.getsockname()[0]); s.close()')

if [ -z "$IP" ]; then
    echo "⚠️  Could not detect LAN IP. Falling back to localhost."
    IP="127.0.0.1"
fi

echo "🛑  Stopping existing instances..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:9999 | xargs kill -9 2>/dev/null

echo "🚀  Starting MeshCloud on LAN IP: $IP"
echo "    - Dashboard: http://$IP:8000/dashboard"
echo "    - API Docs:  http://$IP:8000/docs"
echo "    - Other devices should see this node automatically if on the same WiFi/Network."

# 2. Export variables with the LAN IP
export NODE_URL="http://$IP:8000"
export VERIFY_SSL="false"

# 3. Install dependencies quietly
pip install -r requirements.txt > /dev/null 2>&1

# 4. Start the server
uvicorn meshcloud.main:app --host 0.0.0.0 --port 8000 --reload