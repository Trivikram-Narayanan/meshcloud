#!/usr/bin/env bash
# setup.sh — One-shot setup for MeshCloud
# Run this once after cloning the repo.
# Usage: ./setup.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

# ── colours ───────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓ $*${NC}"; }
warn() { echo -e "${YELLOW}  ! $*${NC}"; }
die()  { echo -e "${RED}  ✗ $*${NC}"; exit 1; }

echo ""
echo "=================================================="
echo "  MeshCloud — local setup"
echo "=================================================="
echo ""

# ── 1. Python version check ───────────────────────────────────────────────
echo "Checking Python..."
PYTHON=$(command -v python3 || command -v python || die "Python not found. Install Python 3.9+")
PY_VER=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$("$PYTHON" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PYTHON" -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
  die "Python 3.9+ required (found $PY_VER)"
fi
ok "Python $PY_VER"

# ── 2. Virtual environment ────────────────────────────────────────────────
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d "$REPO/venv" ]; then
  "$PYTHON" -m venv "$REPO/venv"
  ok "Created venv"
else
  ok "venv already exists"
fi

source "$REPO/venv/bin/activate"

echo "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "Python dependencies installed"

# ── 3. .env file ─────────────────────────────────────────────────────────
echo ""
echo "Configuring environment..."
if [ ! -f "$REPO/.env" ]; then
  cp "$REPO/.env.example" "$REPO/.env"

  # Generate secure random values
  ENC_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  JWT_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  NODE_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))")

  # Replace placeholders (works on both Linux and macOS)
  sed -i.bak "s|your-32-byte-hex-encryption-key-here|$ENC_KEY|g" "$REPO/.env"
  sed -i.bak "s|your-super-secret-jwt-key-here-at-least-32-characters-long|$JWT_KEY|g" "$REPO/.env"
  sed -i.bak "s|your-secure-node-token-here|$NODE_TOKEN|g" "$REPO/.env"
  sed -i.bak "s|changeme|meshcloud123|g" "$REPO/.env"
  rm -f "$REPO/.env.bak"

  ok ".env created with auto-generated secrets"
  warn "Admin password set to 'meshcloud123' — change it in .env before exposing to a network"
else
  ok ".env already exists (skipping)"
fi

# ── 4. Storage directories ────────────────────────────────────────────────
echo ""
echo "Creating storage directories..."
mkdir -p storage/tmp storage/chunks storage/manifests
ok "Storage directories ready"

# ── 5. Frontend build ─────────────────────────────────────────────────────
echo ""
echo "Building React dashboard..."
if command -v npm &>/dev/null; then
  cd "$REPO/frontend"
  npm install --silent
  npm run build --silent
  cd "$REPO"
  ok "Dashboard built"
else
  warn "npm not found — skipping frontend build. The app will use the built-in fallback UI."
  warn "Install Node.js from https://nodejs.org and re-run this script to get the full dashboard."
fi

# ── 6. Done ───────────────────────────────────────────────────────────────
echo ""
echo "=================================================="
echo -e "${GREEN}  Setup complete!${NC}"
echo "=================================================="
echo ""
echo "  To start a single node:"
echo "    ./start.sh"
echo ""
echo "  To start a 3-node mesh on your machine:"
echo "    ./start_mesh.sh"
echo ""
echo "  Dashboard will be at:  http://localhost:8000"
echo "  API docs at:           http://localhost:8000/docs"
echo ""
echo "  Your secrets are in .env — keep it private."
echo ""
