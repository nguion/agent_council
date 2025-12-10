#!/bin/bash
# Start Agent Council Frontend

echo "🚀 Starting Agent Council Frontend..."
echo ""

cd web-ui

# Check if node_modules exists
if [ ! -d node_modules ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    echo "VITE_API_URL=http://localhost:8000" > .env
fi

echo "✅ Environment ready!"
echo ""
echo "🌐 Frontend will be available at: http://localhost:5173"
echo "🔌 Connecting to API at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the dev server
npm run dev
