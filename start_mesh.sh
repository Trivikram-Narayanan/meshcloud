#!/usr/bin/env bash
# start_mesh.sh — Starts a 3-node MeshCloud cluster for local testing
# Usage: ./start_mesh.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
VENV="$REPO/venv/bin/activate"

# ── cleanup previous runs ──────────────────────────────────────────────────
pkill -f "uvicorn meshcloud.main" 2>/dev/null || true
sleep 1

# ── storage dirs ───────────────────────────────────────────────────────────
for port in 8000 8001 8002; do
  dir="$REPO/storage_node$port"
  mkdir -p "$dir/tmp" "$dir/chunks" "$dir/manifests"
done

# ── peers: each node knows the others ─────────────────────────────────────
# Node A (8000) knows B (8001) and C (8002)
cat > "$REPO/config/peers_8000.json" <<'JSON'
{"peers":["http://localhost:8001","http://localhost:8002"]}
JSON

# Node B (8001) knows A (8000) and C (8002)
cat > "$REPO/config/peers_8001.json" <<'JSON'
{"peers":["http://localhost:8000","http://localhost:8002"]}
JSON

# Node C (8002) knows A (8000) and B (8001)
cat > "$REPO/config/peers_8002.json" <<'JSON'
{"peers":["http://localhost:8000","http://localhost:8001"]}
JSON

echo "[start_mesh] Launching Node A on port 8000..."
cd "$REPO"
source "$VENV"

# Clear all pycache to ensure fresh load
find "$REPO/meshcloud" -name "*.pyc" -delete 2>/dev/null || true
find "$REPO/meshcloud" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

NODE_URL=http://localhost:8000 \
NODE_ID=node-A \
STORAGE_DIR=storage_node8000 \
PEERS_FILE=config/peers_8000.json \
LOG_LEVEL=info \
uvicorn meshcloud.main:app --host 0.0.0.0 --port 8000 \
  > /tmp/node8000.log 2>&1 &
echo "  → Node A PID: $!"

sleep 1

echo "[start_mesh] Launching Node B on port 8001..."
NODE_URL=http://localhost:8001 \
NODE_ID=node-B \
STORAGE_DIR=storage_node8001 \
PEERS_FILE=config/peers_8001.json \
LOG_LEVEL=info \
uvicorn meshcloud.main:app --host 0.0.0.0 --port 8001 \
  > /tmp/node8001.log 2>&1 &
echo "  → Node B PID: $!"

sleep 1

echo "[start_mesh] Launching Node C on port 8002..."
NODE_URL=http://localhost:8002 \
NODE_ID=node-C \
STORAGE_DIR=storage_node8002 \
PEERS_FILE=config/peers_8002.json \
LOG_LEVEL=info \
uvicorn meshcloud.main:app --host 0.0.0.0 --port 8002 \
  > /tmp/node8002.log 2>&1 &
echo "  → Node C PID: $!"

echo ""
echo "[start_mesh] Waiting for all nodes to boot..."
sleep 6

echo ""
echo "[start_mesh] Cluster health check:"
for port in 8000 8001 8002; do
  result=$(curl -s --connect-timeout 2 "http://localhost:$port/health" 2>/dev/null || echo '{"status":"UNREACHABLE"}')
  echo "  Node :$port → $result"
done
echo ""
echo "[start_mesh] Dashboards:"
echo "  Node A: http://localhost:8000/dashboard"
echo "  Node B: http://localhost:8001/dashboard"
echo "  Node C: http://localhost:8002/dashboard"
echo ""
echo "[start_mesh] Logs: /tmp/node{8000,8001,8002}.log"
