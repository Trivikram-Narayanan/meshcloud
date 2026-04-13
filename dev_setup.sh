#!/bin/bash
set -e

echo "🚀 Starting MeshCloud Development Setup..."

# --- Python Client Setup ---
if [ -d "clients/python" ]; then
    echo "------------------------------------------------"
    echo "🐍 Setting up Python Client..."
    cd clients/python
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "   Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate and install
    source venv/bin/activate
    echo "   Installing dependencies..."
    pip install -e ".[dev]"
    
    echo "   Running tests..."
    pytest
    
    deactivate
    cd ../..
else
    echo "⚠️  'clients/python' directory not found. Skipping Python setup."
fi

# --- JavaScript/Frontend Setup ---
# Checking both 'clients/javascript' (from README) and 'frontend' (from file context)
JS_DIR=""
if [ -d "clients/javascript" ]; then
    JS_DIR="clients/javascript"
elif [ -d "frontend" ]; then
    JS_DIR="frontend"
fi

if [ -n "$JS_DIR" ]; then
    echo "------------------------------------------------"
    echo "🌐 Setting up JavaScript Client/Frontend in $JS_DIR..."
    cd "$JS_DIR"
    npm install
    npm test
    cd ../..
fi

echo "------------------------------------------------"
echo "✅ Setup and checks complete!"