# 🤖 AI Voice Sales Agent - Complete System Setup & Usage Guide

This guide will help you set up and run your complete AI Voice Sales Agent system with backend, frontend, and RAG (Retrieval-Augmented Generation) support.

## 🏗️ System Architecture

Your system consists of:
- **Backend**: Python agent with LiveKit, Google AI, and RAG capabilities
- **Frontend**: Next.js web interface for voice/video chat
- **RAG System**: ChromaDB with company documents (FAQ, Products, Orders)
- **Memory**: Mem0 for conversation persistence

## 📋 Prerequisites

### 1. Python Environment
- Python 3.8+ installed
- Virtual environment activated: `source ai/bin/activate`

### 2. Node.js Environment  
- Node.js 18+ installed
- npm or pnpm package manager

### 3. API Keys (already configured in your .env)
- ✅ Google API Key
- ✅ LiveKit credentials
- ✅ Mem0 API Key

## 🚀 Quick Start (Recommended)

### Option 1: Run Everything at Once
```bash
# Start both backend and frontend
./run_system.sh
```

### Option 2: Run Components Separately

#### Start Backend Only:
```bash
./run_backend.sh
```

#### Start Frontend Only:
```bash
./run_frontend.sh
```

## 🔧 Manual Setup (If needed)

### Backend Setup
```bash
# Activate virtual environment
source ai/bin/activate

# Ensure RAG system is set up
python setup_knowledge_base.py

# Start the enhanced agent
python agent_with_rag_example.py dev
```

### Frontend Setup
```bash
# Navigate to UI directory
cd UI

# Install dependencies
pnpm install  # or npm install

# Start development server
pnpm dev  # or npm run dev
```

## 🌐 Accessing Your Application

Once both services are running:

1. **Open your browser** and go to: `http://localhost:3000`
2. **Wait 10-30 seconds** for both services to fully initialize
3. **Click "Connect"** to join the voice chat room
4. **Start talking** with your AI sales agent!

## 🤖 Features Available

### 💬 Conversational AI
- Real-time voice conversations
- Google AI-powered responses
- Natural language processing

### 📚 RAG-Powered Knowledge
- Instant access to company FAQ
- Product details and specifications
- Pricing and order information
- Contextual responses from documents

### 🧠 Memory System
- Remembers previous conversations
- Personalized responses for user "Kundan"
- Persistent conversation history

### 🎥 Advanced Voice Features
- Real-time video chat
- Noise cancellation
- High-quality audio processing

## 📊 RAG System Details

Your RAG system includes:

### Document Types
- **FAQ**: Company support and help information
- **Products**: DD solution features and specifications  
- **Orders**: Pricing plans and ordering process

### Current Status
- ✅ **3 documents** processed
- ✅ **Vector database** ready
- ✅ **Semantic search** operational

### Test RAG System
```bash
# Run RAG tests
python setup_knowledge_base.py --test

# Validate setup
python setup_knowledge_base.py --validate
```

## 🔍 Troubleshooting

### Backend Issues

#### "Virtual environment 'ai' not found"
```bash
python -m venv ai
source ai/bin/activate
pip install -r requirements.txt
```

#### "RAG database not found"
```bash
python setup_knowledge_base.py
```

#### "Import errors"
```bash
source ai/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

#### "Node modules not found"
```bash
cd UI
npm install  # or pnpm install
```

#### "Port 3000 in use"
```bash
# Kill any process using port 3000
sudo lsof -ti:3000 | xargs kill -9

# Or use a different port
cd UI
npm run dev -- -p 3001
```

### RAG System Issues

#### "No context found for queries"
```bash
# Check if documents exist
ls -la data/documents/

# Rebuild RAG database
python setup_knowledge_base.py --force
```

## 📁 Project Structure

```
├── agent_with_rag_example.py    # Enhanced agent with RAG
├── rag/                         # RAG system modules
│   ├── knowledge_manager.py     # Document management
│   ├── vector_store.py          # ChromaDB interface
│   ├── retrieval_system.py      # Smart retrieval
│   └── document_processor.py    # PDF processing
├── UI/                          # Next.js frontend
├── data/documents/              # Company documents
├── chroma_db/                   # Vector database
├── run_system.sh               # Complete system runner
├── run_backend.sh              # Backend runner
└── run_frontend.sh             # Frontend runner
```

## 🎯 Usage Tips

### Best Practices
1. **Always start backend first** if running separately
2. **Wait for initialization** before testing
3. **Check logs** if something doesn't work
4. **Use Ctrl+C** to stop services cleanly

### Example Conversations
Try asking your agent:
- "What are your pricing plans?"
- "How does the DD solution work?"
- "How do I get support?"
- "What features are included?"

### RAG Enhancement
- The agent now provides **accurate, document-based answers**
- Responses include **company-specific information**
- **Contextual retrieval** based on query type

## 🔄 System Workflow

1. **User speaks** → Frontend captures audio
2. **LiveKit** → Streams to backend agent  
3. **Agent processes** → Query understanding
4. **RAG retrieval** → Searches company documents
5. **Google AI** → Generates contextual response
6. **Memory storage** → Saves conversation
7. **Response delivery** → Back to user

## 📞 Support

If you encounter issues:
1. Check the console logs in both terminal windows
2. Verify all services are running on correct ports
3. Ensure your API keys are valid
4. Test the RAG system separately if needed

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Backend shows "RAG system initialized with 3 documents"
- ✅ Frontend loads at http://localhost:3000
- ✅ "Connect" button works without errors
- ✅ Agent responds with company-specific information
- ✅ Conversations are remembered across sessions

---

🎊 **Congratulations!** Your AI Voice Sales Agent with RAG support is now operational!