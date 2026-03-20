#!/bin/bash

echo "🛑  Stopping any existing MeshCloud instances..."
# Kill process on port 8000 (API) and 9999 (Discovery)
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:9999 | xargs kill -9 2>/dev/null

echo "🧹  Cleaning development database..."
# Remove local DB to prevent protocol mismatch errors (HTTPS vs HTTP)
rm -f db/meshcloud.db

echo "📦  Checking dependencies..."
pip install -r requirements.txt

echo "🚀  Starting MeshCloud Node..."
echo "    - Dashboard: http://localhost:8000/dashboard"
echo "    - API Docs:  http://localhost:8000/docs"

# Set environment variables for local dev
export NODE_URL="http://localhost:8000"
export VERIFY_SSL="false"

uvicorn meshcloud.main:app --host 0.0.0.0 --port 8000 --reload