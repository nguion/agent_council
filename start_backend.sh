#!/bin/bash
# Start Agent Council Backend API

echo "🚀 Starting Agent Council Backend API..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env with your OPENAI_API_KEY"
    echo ""
    echo "Example:"
    echo "  echo 'OPENAI_API_KEY=your-key-here' > .env"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "📦 Virtual environment not found. Creating..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Check if requirements are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt
    pip install -q -r requirements-web.txt
fi

echo "✅ Environment ready!"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🌐 Frontend should connect to: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the API
python run_api.py
