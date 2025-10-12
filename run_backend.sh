#!/bin/bash

# AI Voice Sales Agent - Backend Runner with RAG Support
# This script starts the backend agent with enhanced RAG capabilities

echo "🚀 Starting AI Voice Sales Agent Backend with RAG Support"
echo "=========================================================="

# Check if virtual environment exists
if [ -d "ai" ]; then
    echo "📦 Activating virtual environment..."
    source ai/bin/activate
else
    echo "⚠️  Virtual environment 'ai' not found. Make sure to create it first:"
    echo "   python -m venv ai"
    echo "   source ai/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your API keys:"
    echo "   GOOGLE_API_KEY=your_google_api_key"
    echo "   LIVEKIT_URL=your_livekit_url"
    echo "   LIVEKIT_API_KEY=your_livekit_api_key"
    echo "   LIVEKIT_API_SECRET=your_livekit_api_secret"
    echo "   MEM0_API_KEY=your_mem0_api_key"
    exit 1
fi

# Check if RAG system is set up
echo "🔍 Checking RAG system setup..."
if [ -d "chroma_db" ]; then
    echo "✅ RAG database found"
else
    echo "⚠️  RAG database not found. Setting it up..."
    python setup_knowledge_base.py
    if [ $? -ne 0 ]; then
        echo "❌ RAG setup failed. Please run manually:"
        echo "   python setup_knowledge_base.py"
        exit 1
    fi
fi

echo "🔥 Starting the enhanced agent with RAG capabilities..."
echo "💡 The agent now has access to company documents (FAQ, Products, Orders)"
echo "🌐 Frontend will be available at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the agent"
echo "=========================================================="

# Start the agent with RAG support
python agent_with_rag_example.py dev