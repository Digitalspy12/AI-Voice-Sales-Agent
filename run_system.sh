#!/bin/bash

# AI Voice Sales Agent - Complete System Runner
# This script starts both backend and frontend components

echo "🤖 AI Voice Sales Agent - Complete System Startup"
echo "=================================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down system..."
    kill $(jobs -p) 2>/dev/null
    wait
    echo "✅ System stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Check prerequisites
echo "🔍 Checking system prerequisites..."

# Check if virtual environment exists
if [ ! -d "ai" ]; then
    echo "❌ Virtual environment 'ai' not found"
    echo "Please set up the Python environment first:"
    echo "  python -m venv ai"
    echo "  source ai/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your API keys"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Make scripts executable
chmod +x run_backend.sh
chmod +x run_frontend.sh

echo "🚀 Starting system components..."
echo ""

# Start backend in background
echo "🔧 Starting backend (Agent with RAG)..."
./run_backend.sh &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "🎨 Starting frontend (Next.js UI)..."
./run_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "🎉 System is starting up!"
echo "=================================================="
echo "🤖 Backend (Agent + RAG): Starting..."
echo "🌐 Frontend (Next.js): Starting..."
echo ""
echo "🔗 Once ready, access your application at:"
echo "   http://localhost:3000"
echo ""
echo "🤖 Features available:"
echo "   ✅ Voice conversation with AI agent"
echo "   ✅ RAG-powered responses from company documents"
echo "   ✅ Memory persistence across sessions"
echo "   ✅ Real-time video chat"
echo "   ✅ Noise cancellation"
echo ""
echo "⏱️  Please wait 10-30 seconds for both services to fully start..."
echo ""
echo "Press Ctrl+C to stop the entire system"
echo "=================================================="

# Wait for both processes
wait