#!/usr/bin/env bash
# start.sh — Start a single MeshCloud node
# Run ./setup.sh first if you haven't already.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

# Load .env if present
if [ -f "$REPO/.env" ]; then
  set -o allexport
  source "$REPO/.env"
  set +o allexport
else
  echo "Warning: .env not found. Run ./setup.sh first."
fi

# Activate venv
if [ ! -d "$REPO/venv" ]; then
  echo "Virtual environment not found. Run ./setup.sh first."
  exit 1
fi
source "$REPO/venv/bin/activate"

# Stop anything already on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Defaults for local dev if not set in .env
export NODE_URL="${NODE_URL:-http://localhost:8000}"
export STORAGE_DIR="${STORAGE_DIR:-storage}"

echo ""
echo "Starting MeshCloud..."
echo "  Dashboard: http://localhost:8000"
echo "  API docs:  http://localhost:8000/docs"
echo ""

uvicorn meshcloud.main:app --host 0.0.0.0 --port 8000 --reload
