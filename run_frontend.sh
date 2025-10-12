#!/bin/bash

# AI Voice Sales Agent - Frontend Runner
# This script starts the Next.js frontend interface

echo "🎨 Starting AI Voice Sales Agent Frontend"
echo "=========================================="

# Check if UI directory exists
if [ ! -d "UI" ]; then
    echo "❌ UI directory not found"
    exit 1
fi

cd UI

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    
    # Check if pnpm is available
    if command -v pnpm &> /dev/null; then
        echo "Using pnpm..."
        pnpm install
    elif command -v npm &> /dev/null; then
        echo "Using npm..."
        npm install
    else
        echo "❌ Neither npm nor pnpm found. Please install Node.js"
        exit 1
    fi
fi

# Check if .env.local exists, create it if not
if [ ! -f ".env.local" ]; then
    echo "🔧 Creating .env.local file..."
    cat > .env.local << EOF
# LiveKit Configuration
LIVEKIT_URL=wss://team-ykundan-ik3dy4a5.livekit.cloud
LIVEKIT_API_KEY=APIHtX5mhLRBWdy
LIVEKIT_API_SECRET=BfxaUwPBjgQBnElTnTuJ0ocRhexD9HfS5TyweOVZXjdC

# Next.js Configuration
NEXT_PUBLIC_LIVEKIT_URL=wss://team-ykundan-ik3dy4a5.livekit.cloud
EOF
    echo "✅ Created .env.local with LiveKit configuration"
fi

echo "🌐 Starting Next.js development server..."
echo "📱 Frontend will be available at: http://localhost:3000"
echo "🎤 Make sure the backend is running for full functionality"
echo ""
echo "Press Ctrl+C to stop the frontend"
echo "=========================================="

# Start the frontend
if command -v pnpm &> /dev/null; then
    pnpm dev
else
    npm run dev
fi