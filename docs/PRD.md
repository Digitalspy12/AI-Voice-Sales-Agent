# DD Solution Sales Agent - Project Documentation

## Project Overview

This is an **AI-powered voice sales agent** designed to handle customer inquiries about a Due Diligence (DD) solution. The agent combines real-time voice conversation with intelligent business context to provide personalized sales support and product information to prospects.

### Core Vision
Build an intelligent, conversational sales assistant that can engage with prospects through voice, understand their business needs, answer company-specific questions, and guide them through the sales process—all while maintaining conversation history and context.

---

## Architecture Overview

### Technology Stack

**Backend:**
- **Framework**: LiveKit (real-time voice/video AI agent framework)
- **LLM**: Google Realtime API with voice synthesis
- **Memory System**: mem0 (stores conversation history and user context)
- **Vector DB**: Chroma (RAG-based document retrieval - being added)
- **Language**: Python

**Frontend:**
- **Framework**: React (UI for voice agent interaction)
- **Communication**: LiveKit WebRTC connection to backend

**Core Backend Files:**

1. **`prompts.py`** - Agent instructions and personality
2. **`agent.py`** - Main agent logic, session management, memory integration

---

## Current System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      React UI (Frontend)                        │
│                  (Voice/Video Interface)                        │
└─────────────────┬───────────────────────────────────────────────┘
                  │ WebRTC Connection
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                   LiveKit Framework                             │
│              (Voice Agent Session Management)                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    ↓                           ↓
┌──────────────────┐      ┌──────────────────┐
│  prompts.py      │      │   agent.py       │
│                  │      │                  │
│ - Agent Persona  │      │ - Session Init   │
│   (Aria)         │      │ - Chat Context   │
│ - Instructions   │      │ - Memory Mgmt    │
│ - System Prompt  │      │ - Shutdown Hook  │
└──────────────────┘      └────────┬─────────┘
                                   │
                          ┌────────┴─────────┐
                          ↓                  ↓
                    ┌──────────────┐   ┌──────────────┐
                    │ Google LLM   │   │ mem0 Client  │
                    │ (Realtime)   │   │ (Memory DB)  │
                    │ - Voice      │   │              │
                    │ - Response   │   │ Stores:      │
                    │ - Generation │   │ - Chat hist  │
                    └──────────────┘   │ - User ctx   │
                                       └──────────────┘
```

---

## Current Features

### 1. Voice-Based Sales Agent
- Real-time voice interaction using Google Realtime API
- Noise cancellation (BVC enhancement)
- Professional sales-focused persona named "Aria"
- Warm, approachable, solution-oriented communication style

### 2. Conversation Memory (mem0 Integration)
- **What it stores**: Conversation history between agent and user
- **How it works**: 
  - On session start: Retrieves all previous conversations for the user
  - During session: Tracks all user/agent messages
  - On shutdown: Saves new conversation context to mem0
- **Current use**: Personalizes responses based on previous interactions with user "Kundan"

### 3. Agent Instructions & Persona
- Defined in `prompts.py` with two instruction sets:
  - `AGENT_INSTRUCTION`: System prompt defining Aria's personality, role, and approach
  - `SESSION_INSTRUCTION`: Opening greeting and session initialization
- Focuses on DD solution sales with inquiry categories covering features, pricing, use cases, etc.

### 4. Live Chat Context Management
- Dynamic chat context building in `agent.py`
- Memory filtering to avoid redundancy
- Proper message formatting (user/assistant roles)
- Shutdown callback to persist conversations

---

## New Features Being Added

### 1. **Chroma DB Integration (RAG - Retrieval Augmented Generation)**

**Purpose**: Retrieve company-specific documentation to augment agent responses

**What will be stored:**
- FAQ documents (common customer questions and answers)
- Product details (DD solution features, capabilities, benefits)
- Order/pricing information (packages, pricing tiers, payment terms)

**How it works:**
- PDFs are parsed into text chunks and embedded as vectors
- When user asks a question, Chroma performs semantic search
- Top-matching documents are retrieved and injected into chat context
- Agent responds using both retrieved docs + training knowledge

**Integration flow:**
```
User Query → Chroma Vector Search → Retrieved Docs → 
Chat Context → LLM Generation → Response with company info
```

**Benefits:**
- Ensures consistent, accurate product information
- No hallucinations about pricing or features
- Scales easily as docs are updated
- Separates static knowledge (docs) from dynamic memory (conversations)

### 2. **Company Knowledge Base**

**Components:**

**FAQ Document**
- Common questions about DD solution
- Troubleshooting and setup guidance
- General inquiries about service

**Product Details Document**
- Core features and capabilities
- Use cases and industry applications
- Implementation timeline
- Security and compliance standards
- Competitive advantages

**Order/Pricing Document**
- Pricing tiers and packages
- Add-on services and costs
- License terms
- Payment options
- Discount structures

**Implementation:**
- Parse PDFs into structured text chunks (250-500 words each)
- Index with Chroma for semantic search
- Tag with metadata (document type, category, date)

### 3. **Enhanced Response Context**

**Current state**: Agent uses mem0 memory only
**After enhancement**: Agent uses mem0 + Chroma together

**Example flow:**

*Scenario: Prospect asks "What's your pricing for SMBs?"*

- **mem0 provides**: "This is ABC Corp, evaluating for market entry in APAC region"
- **Chroma provides**: "SMB Package: $5K/month, includes 5 concurrent users, basic analytics"
- **Agent responds**: "ABC Corp, based on your market entry focus in APAC, our SMB Package at $5K/month includes 5 concurrent users and basic analytics. Given your region, we also offer localized support..."

---

## System Data Flow

### Session Initialization
```
1. User starts React UI → Creates LiveKit connection
2. Backend loads initial context:
   - Agent instructions from prompts.py
   - User memories from mem0 (if exists)
   - [NEW] Company knowledge from Chroma
3. Session starts with combined context
4. Agent generates opening greeting
```

### During Conversation
```
1. User speaks (voice input)
2. LiveKit captures and transcribes
3. Query routed to:
   a. mem0 → Retrieves user conversation history
   b. Chroma → Retrieves relevant company docs [NEW]
   c. Chat Context → Combines all information
4. Google LLM generates response with full context
5. Response synthesized to voice via agent
6. Logged and tracked
```

### Session Shutdown
```
1. User ends conversation
2. Shutdown hook triggered
3. New messages extracted from chat context
4. Messages saved to mem0 (user conversation history)
5. Session ends
```

---

## File Structure

```
project/
├── prompts.py                 # Agent persona and instructions
│   ├── AGENT_INSTRUCTION     # Aria's system prompt
│   └── SESSION_INSTRUCTION   # Opening greeting
│
├── agent.py                   # Main agent logic
│   ├── Assistant class        # Agent configuration
│   ├── entrypoint()          # Session initialization
│   ├── shutdown_hook()       # Memory persistence
│   └── LiveKit integration   # Voice/video setup
│
├── .env                       # Environment variables
│   ├── GOOGLE_API_KEY
│   ├── MEM0_API_KEY
│   └── LiveKit credentials
│
└── frontend/                  # React UI
    └── components/
        └── AgentInterface    # Voice chat UI
```

---

## Configuration Details

### prompts.py Configuration

**Agent Persona**:
- Name: Aria
- Role: DD solution sales specialist
- Tone: Professional yet approachable
- Temperature: 0.3 (focused, consistent responses)
- Voice: "aoede" (Google voice)

**Key responsibilities**:
- Address DD solution inquiries
- Identify business needs
- Provide relevant examples
- Guide toward next steps

### agent.py Configuration

**Voice Settings**:
- Video enabled
- BVC noise cancellation (LiveKit Cloud)
- Real-time model with 0.3 temperature

**Memory Configuration**:
- User ID: "kundan"
- Memory system: mem0 AsyncMemoryClient
- On-shutdown auto-save enabled

---

## Upcoming Integration Points

### Adding Chroma DB

**Required changes**:

1. **Update `.env`**:
   - Add Chroma connection string (local or cloud)

2. **Modify `agent.py`**:
   - Initialize Chroma client on startup
   - Add document retrieval before context building
   - Inject retrieved docs into ChatContext

3. **New utility file** (proposed `knowledge_base.py`):
   - PDF parsing and chunking
   - Vector embedding
   - Chroma indexing
   - Search and retrieval functions

4. **Document preparation**:
   - Parse FAQ, product details, order info PDFs
   - Create embeddings
   - Index in Chroma

---

## Benefits of This Architecture

1. **Voice-First Sales**: Natural, conversational sales experience
2. **Contextual Awareness**: Remembers user history + company knowledge
3. **Accurate Information**: Company docs prevent hallucinations
4. **Scalability**: Easy to add new documents or users
5. **Real-time**: No latency, immediate responses
6. **Persistent Memory**: Conversations stored for follow-ups
7. **Professional**: Guided by sales-focused instructions

---

## Next Steps

1. **Prepare company documents**:
   - Extract and structure FAQ PDF
   - Extract and structure product details PDF
   - Extract and structure order/pricing PDF

2. **Set up Chroma DB**:
   - Install Chroma locally or cloud
   - Configure connection

3. **Implement knowledge base module**:
   - Parse PDFs
   - Create embeddings
   - Index documents

4. **Integrate with agent.py**:
   - Load Chroma on startup
   - Retrieve docs on queries
   - Inject into context

5. **Test and refine**:
   - Test voice conversations with various queries
   - Validate doc retrieval accuracy
   - Optimize prompts based on responses

---

## Success Metrics

- Accurate answers to FAQ questions (from docs)
- Consistent pricing information in responses
- User satisfaction with sales guidance
- Proper context retention across sessions
- Fast response times (< 2 seconds)