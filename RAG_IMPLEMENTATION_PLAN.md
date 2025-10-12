# RAG Implementation Plan for Company Data Integration

## 🎯 Project Goal
Implement Retrieval Augmented Generation (RAG) to integrate company PDF documents (FAQ, Product Details, Order Information) into the AI Voice Sales Agent, enabling accurate, document-grounded responses without hallucinations.

## 📋 Implementation Overview

### Current State
- ✅ Agent with mem0 for conversation memory
- ✅ Google Realtime API for voice interaction
- ✅ LiveKit framework for real-time communication
- ❌ No company document integration
- ❌ Potential hallucinations about company info

### Target State
- ✅ RAG-enhanced agent with company knowledge
- ✅ Document-grounded responses
- ✅ Semantic search across FAQ, products, orders
- ✅ Combined mem0 + ChromaDB context
- ✅ Zero hallucinations on company data

---

## 🗺️ Implementation Roadmap

### Phase 1: Infrastructure Setup (Days 1-2)
**Goal**: Set up ChromaDB and document processing infrastructure

#### 1.1 Install Dependencies
```bash
# Add to requirements.txt
chromadb>=0.4.15
pypdf2>=3.0.1
sentence-transformers>=2.2.2
langchain>=0.1.0
langchain-community>=0.0.10
python-dotenv>=1.0.0
```

#### 1.2 Create Directory Structure
```
project/
├── data/
│   ├── documents/           # Source PDF files
│   │   ├── faq.pdf
│   │   ├── product_details.pdf
│   │   └── order_info.pdf
│   └── processed/           # Processed chunks and metadata
├── rag/
│   ├── __init__.py
│   ├── document_processor.py    # PDF parsing and chunking
│   ├── vector_store.py          # ChromaDB operations
│   ├── retrieval_system.py     # Search and retrieval
│   └── knowledge_manager.py    # Document management utilities
└── tests/
    └── test_rag.py             # RAG system tests
```

#### 1.3 ChromaDB Setup
```python
# rag/vector_store.py
import chromadb
from chromadb.config import Settings

class CompanyKnowledgeBase:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collections = {
            "faq": self.client.get_or_create_collection("company_faq"),
            "products": self.client.get_or_create_collection("product_details"),
            "orders": self.client.get_or_create_collection("order_info")
        }
```

### Phase 2: Document Processing Pipeline (Days 3-4)
**Goal**: Build robust PDF parsing and text chunking system

#### 2.1 PDF Parser Implementation
```python
# rag/document_processor.py
import PyPDF2
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple

class DocumentProcessor:
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """Split text into overlapping chunks with metadata"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "text": chunk_text,
                "chunk_id": f"chunk_{i//chunk_size}",
                "start_index": i,
                "word_count": len(chunk_words)
            })
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        return self.embedder.encode(texts).tolist()
```

#### 2.2 Document Category Mapping
```python
# Document processing configuration
DOCUMENT_CONFIG = {
    "faq": {
        "file_path": "data/documents/faq.pdf",
        "chunk_size": 300,
        "collection": "company_faq",
        "metadata": {"type": "faq", "category": "support"}
    },
    "products": {
        "file_path": "data/documents/product_details.pdf", 
        "chunk_size": 400,
        "collection": "product_details",
        "metadata": {"type": "product", "category": "features"}
    },
    "orders": {
        "file_path": "data/documents/order_info.pdf",
        "chunk_size": 350, 
        "collection": "order_info",
        "metadata": {"type": "order", "category": "pricing"}
    }
}
```

### Phase 3: Vector Storage & Retrieval (Days 5-6)
**Goal**: Implement semantic search and document retrieval

#### 3.1 Vector Storage System
```python
# rag/vector_store.py (continued)
class CompanyKnowledgeBase:
    def store_documents(self, doc_type: str, chunks: List[Dict], embeddings: List[List[float]]):
        """Store document chunks with embeddings"""
        collection = self.collections[doc_type]
        
        ids = [f"{doc_type}_{chunk['chunk_id']}" for chunk in chunks]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [
            {
                **chunk,
                "document_type": doc_type,
                "created_at": datetime.now().isoformat()
            } 
            for chunk in chunks
        ]
        
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def search_documents(self, query: str, doc_types: List[str] = None, n_results: int = 5) -> Dict:
        """Search across document collections"""
        if doc_types is None:
            doc_types = list(self.collections.keys())
            
        all_results = {}
        
        for doc_type in doc_types:
            collection = self.collections[doc_type]
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            all_results[doc_type] = results
            
        return all_results
```

#### 3.2 Smart Retrieval System
```python
# rag/retrieval_system.py
class SmartRetriever:
    def __init__(self, knowledge_base: CompanyKnowledgeBase):
        self.kb = knowledge_base
        self.query_classifiers = {
            "faq": ["how", "what", "why", "help", "problem", "issue", "question"],
            "products": ["feature", "capability", "product", "solution", "service"],
            "orders": ["price", "cost", "order", "buy", "purchase", "payment", "plan"]
        }
    
    def classify_query(self, query: str) -> List[str]:
        """Determine which document types are most relevant"""
        query_lower = query.lower()
        relevant_types = []
        
        for doc_type, keywords in self.query_classifiers.items():
            if any(keyword in query_lower for keyword in keywords):
                relevant_types.append(doc_type)
        
        # If no specific type detected, search all
        return relevant_types if relevant_types else list(self.query_classifiers.keys())
    
    def retrieve_context(self, query: str, max_context_length: int = 2000) -> str:
        """Retrieve and format relevant context for the query"""
        relevant_types = self.classify_query(query)
        search_results = self.kb.search_documents(query, relevant_types, n_results=3)
        
        context_parts = []
        current_length = 0
        
        for doc_type, results in search_results.items():
            if not results['documents'][0]:  # Skip empty results
                continue
                
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                if current_length + len(doc) > max_context_length:
                    break
                    
                context_parts.append(f"[{doc_type.upper()}] {doc}")
                current_length += len(doc)
        
        return "\n\n".join(context_parts)
```

### Phase 4: Agent Integration (Days 7-8)
**Goal**: Integrate RAG system with existing voice agent

#### 4.1 Update Requirements
```bash
# Add to requirements.txt
chromadb>=0.4.15
pypdf2>=3.0.1
sentence-transformers>=2.2.2
```

#### 4.2 Modify Agent Architecture
```python
# Updated agent.py
from rag.vector_store import CompanyKnowledgeBase
from rag.retrieval_system import SmartRetriever

class Assistant(Agent):
    def __init__(self, chat_ctx=None, knowledge_base=None) -> None:
        self.knowledge_base = knowledge_base
        self.retriever = SmartRetriever(knowledge_base) if knowledge_base else None
        
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="aoede",
                temperature=0.3,
            ),
            chat_ctx=chat_ctx
        )
    
    async def generate_response_with_context(self, user_message: str) -> str:
        """Generate response with RAG context"""
        if self.retriever:
            # Get relevant company documents
            company_context = self.retriever.retrieve_context(user_message)
            
            # Add context to chat
            if company_context:
                context_message = f"Relevant company information:\n{company_context}"
                self.chat_ctx.add_message(role="system", content=context_message)
        
        # Generate response with enhanced context
        return await super().generate_response(user_message)
```

#### 4.3 Enhanced Entrypoint with RAG
```python
# Updated entrypoint in agent.py
async def entrypoint(ctx: agents.JobContext):
    # Initialize RAG system
    try:
        knowledge_base = CompanyKnowledgeBase()
        logging.info("RAG system initialized successfully")
    except Exception as e:
        logging.warning(f"RAG system initialization failed: {e}")
        knowledge_base = None
    
    # Rest of existing code...
    initial_ctx = ChatContext()
    
    # Add company knowledge context if available
    if knowledge_base:
        initial_ctx.add_message(
            role="system",
            content="You have access to company documents including FAQ, product details, and order information. Use this information to provide accurate responses."
        )
    
    # Initialize assistant with RAG
    assistant = Assistant(chat_ctx=initial_ctx, knowledge_base=knowledge_base)
```

### Phase 5: Document Management System (Day 9)
**Goal**: Create utilities for managing company documents

#### 5.1 Knowledge Manager
```python
# rag/knowledge_manager.py
class KnowledgeManager:
    def __init__(self):
        self.processor = DocumentProcessor()
        self.knowledge_base = CompanyKnowledgeBase()
    
    def add_document(self, file_path: str, doc_type: str, metadata: Dict = None):
        """Add new document to knowledge base"""
        # Extract and process document
        text = self.processor.extract_pdf_text(file_path)
        chunks = self.processor.chunk_text(text)
        embeddings = self.processor.generate_embeddings([chunk['text'] for chunk in chunks])
        
        # Add metadata
        for chunk in chunks:
            chunk.update(metadata or {})
        
        # Store in vector database
        self.knowledge_base.store_documents(doc_type, chunks, embeddings)
        logging.info(f"Added {len(chunks)} chunks from {file_path} to {doc_type} collection")
    
    def refresh_all_documents(self):
        """Refresh all company documents"""
        for doc_type, config in DOCUMENT_CONFIG.items():
            if os.path.exists(config['file_path']):
                self.add_document(
                    config['file_path'], 
                    doc_type, 
                    config['metadata']
                )
    
    def search_test(self, query: str):
        """Test search functionality"""
        retriever = SmartRetriever(self.knowledge_base)
        context = retriever.retrieve_context(query)
        print(f"Query: {query}\n")
        print(f"Retrieved Context:\n{context}")
```

#### 5.2 Setup Script
```python
# setup_knowledge_base.py
from rag.knowledge_manager import KnowledgeManager
import logging

def setup_company_knowledge():
    """Initial setup of company knowledge base"""
    logging.basicConfig(level=logging.INFO)
    
    manager = KnowledgeManager()
    
    # Check if documents exist
    missing_docs = []
    for doc_type, config in DOCUMENT_CONFIG.items():
        if not os.path.exists(config['file_path']):
            missing_docs.append(config['file_path'])
    
    if missing_docs:
        print("Missing documents:")
        for doc in missing_docs:
            print(f"  - {doc}")
        print("Please add these files before running setup.")
        return False
    
    # Process and store all documents
    manager.refresh_all_documents()
    print("✅ Company knowledge base setup complete!")
    return True

if __name__ == "__main__":
    setup_company_knowledge()
```

### Phase 6: Testing & Optimization (Day 10)
**Goal**: Validate and optimize RAG system performance

#### 6.1 Test Suite
```python
# tests/test_rag.py
import pytest
from rag.knowledge_manager import KnowledgeManager

class TestRAGSystem:
    def setup_method(self):
        self.manager = KnowledgeManager()
    
    def test_document_processing(self):
        """Test PDF processing and chunking"""
        # Test with sample documents
        pass
    
    def test_embedding_generation(self):
        """Test embedding quality and consistency"""
        pass
    
    def test_retrieval_accuracy(self):
        """Test retrieval accuracy with known queries"""
        test_queries = [
            "What are your pricing plans?",
            "How do I place an order?", 
            "What features does the DD solution include?",
            "How do I get support?"
        ]
        
        for query in test_queries:
            context = self.manager.search_test(query)
            assert len(context) > 0, f"No context retrieved for: {query}"
    
    def test_query_classification(self):
        """Test query type classification"""
        from rag.retrieval_system import SmartRetriever
        retriever = SmartRetriever(self.manager.knowledge_base)
        
        test_cases = [
            ("What's the pricing?", ["orders"]),
            ("How does the product work?", ["products"]),
            ("I need help with login", ["faq"])
        ]
        
        for query, expected_types in test_cases:
            classified_types = retriever.classify_query(query)
            assert any(t in classified_types for t in expected_types)
```

#### 6.2 Performance Optimization
```python
# Optimization configuration
OPTIMIZATION_CONFIG = {
    "chunk_size": {
        "faq": 300,      # Smaller chunks for specific Q&A
        "products": 400,  # Medium chunks for feature descriptions  
        "orders": 350    # Medium chunks for pricing info
    },
    "retrieval": {
        "max_results": 5,
        "similarity_threshold": 0.7,
        "max_context_length": 2000
    },
    "embeddings": {
        "model": "all-MiniLM-L6-v2",  # Fast and accurate
        "normalize": True
    }
}
```

---

## 🔧 Implementation Steps

### Step 1: Environment Setup
```bash
# Update requirements.txt
echo "chromadb>=0.4.15
pypdf2>=3.0.1  
sentence-transformers>=2.2.2" >> requirements.txt

# Install new dependencies
pip install -r requirements.txt

# Create directory structure
mkdir -p data/documents data/processed rag tests
```

### Step 2: Create Core RAG Files
1. Create `rag/document_processor.py`
2. Create `rag/vector_store.py`  
3. Create `rag/retrieval_system.py`
4. Create `rag/knowledge_manager.py`
5. Create `setup_knowledge_base.py`

### Step 3: Prepare Company Documents
```bash
# Create sample documents (you'll replace these with real ones)
mkdir -p data/documents
# Place your PDFs:
# - data/documents/faq.pdf
# - data/documents/product_details.pdf  
# - data/documents/order_info.pdf
```

### Step 4: Initialize Knowledge Base
```bash
# Run setup script
python setup_knowledge_base.py
```

### Step 5: Update Agent Integration
1. Modify `agent.py` to include RAG system
2. Update prompts to leverage company context
3. Test voice agent with RAG-enhanced responses

### Step 6: Testing & Validation
```bash
# Run tests
pytest tests/test_rag.py -v

# Manual testing
python -c "
from rag.knowledge_manager import KnowledgeManager
manager = KnowledgeManager()
manager.search_test('What are your pricing plans?')
"
```

---

## 📊 Success Metrics

### Technical Metrics
- **Retrieval Accuracy**: >85% relevant documents for queries
- **Response Time**: <2 seconds for document search
- **Context Quality**: No hallucinations on company data
- **Coverage**: All PDF content searchable and retrievable

### Business Metrics  
- **Accurate Pricing**: 100% accurate pricing information
- **FAQ Resolution**: 90%+ of FAQ questions answered correctly
- **Product Information**: Complete product feature coverage
- **Customer Satisfaction**: Improved response quality ratings

---

## 🚨 Risk Mitigation

### Technical Risks
1. **Large PDF Processing**: Implement chunking strategies
2. **Embedding Quality**: Test multiple embedding models
3. **Search Relevance**: Tune similarity thresholds
4. **Memory Usage**: Optimize vector storage

### Integration Risks
1. **Agent Performance**: Monitor response latency
2. **Context Conflicts**: Prioritize company docs over general knowledge
3. **Memory Integration**: Ensure mem0 + ChromaDB work together

---

## 🔄 Maintenance Plan

### Regular Updates
- **Weekly**: Monitor search quality and user feedback
- **Monthly**: Update document embeddings if PDFs change
- **Quarterly**: Optimize chunk sizes and retrieval parameters

### Document Management
- **Version Control**: Track PDF versions and update dates
- **Content Validation**: Verify accuracy of retrieved information
- **Performance Monitoring**: Track search relevance metrics

---

## 🎯 Expected Outcomes

After implementing this RAG system:

1. **Zero Hallucinations**: Agent will only provide information from actual company documents
2. **Accurate Responses**: Pricing, features, and FAQ responses will be 100% accurate
3. **Contextual Understanding**: Agent combines conversation history (mem0) + company knowledge (ChromaDB)
4. **Scalable Knowledge**: Easy to add new documents without retraining
5. **Professional Quality**: Enterprise-grade responses suitable for customer-facing sales

This implementation will transform your voice agent from a general assistant into a specialized company representative with deep, accurate knowledge of your DD solution offerings.