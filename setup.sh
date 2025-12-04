#!/bin/bash
# Agent Council Setup Script
# Sets up virtual environment, installs dependencies, and configures API key

set -e  # Exit on error

echo "🚀 Agent Council Setup"
echo "======================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Install package in editable mode
echo "📦 Installing agent_council package..."
pip install -e . --quiet
echo "✅ Package installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "🔑 Setting up API key..."
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
    
    if [ -n "$api_key" ]; then
        echo "OPENAI_API_KEY=$api_key" > .env
        echo "✅ API key saved to .env"
    else
        echo "⚠️  No API key provided. You'll need to create a .env file with:"
        echo "   OPENAI_API_KEY=sk-..."
    fi
else
    echo "✅ .env file already exists"
fi
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs
echo "✅ Logs directory ready"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "To run Agent Council:"
echo "  source .venv/bin/activate"
echo "  python3 agentcouncil.py"
echo ""

