"""
Vector Store implementation using ChromaDB for company knowledge base.

This module handles the storage and retrieval of document embeddings,
organizing company documents (FAQ, Product Details, Order Info) into
separate collections for efficient semantic search.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class CompanyKnowledgeBase:
    """
    ChromaDB-based knowledge base for storing and retrieving company documents.
    
    Manages three main collections:
    - company_faq: Frequently asked questions and support info
    - product_details: Product features, capabilities, and specifications  
    - order_info: Pricing, packages, and ordering information
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the knowledge base with ChromaDB client.
        
        Args:
            persist_directory: Directory to store ChromaDB data
        """
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        try:
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Create or get collections for different document types
            self.collections = {
                "faq": self.client.get_or_create_collection(
                    name="company_faq",
                    metadata={"description": "Company FAQ and support information"}
                ),
                "products": self.client.get_or_create_collection(
                    name="product_details",
                    metadata={"description": "Product features and specifications"}
                ),
                "orders": self.client.get_or_create_collection(
                    name="order_info", 
                    metadata={"description": "Pricing and ordering information"}
                )
            }
            
            logger.info(f"ChromaDB initialized successfully at {persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def store_documents(self, doc_type: str, chunks: List[Dict], embeddings: List[List[float]]):
        """
        Store document chunks with embeddings in the appropriate collection.
        
        Args:
            doc_type: Type of document ('faq', 'products', 'orders')
            chunks: List of text chunks with metadata
            embeddings: Corresponding embeddings for each chunk
        """
        if doc_type not in self.collections:
            raise ValueError(f"Unknown document type: {doc_type}")
        
        collection = self.collections[doc_type]
        
        # Prepare data for ChromaDB
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
        
        try:
            # Store in ChromaDB
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(chunks)} chunks in {doc_type} collection")
            
        except Exception as e:
            logger.error(f"Failed to store documents in {doc_type}: {e}")
            raise
    
    def search_documents(self, query: str, doc_types: Optional[List[str]] = None, n_results: int = 5) -> Dict:
        """
        Search across document collections using semantic similarity.
        
        Args:
            query: Search query text
            doc_types: List of document types to search (default: all)
            n_results: Maximum number of results per collection
            
        Returns:
            Dictionary with search results for each document type
        """
        if doc_types is None:
            doc_types = list(self.collections.keys())
        
        all_results = {}
        
        for doc_type in doc_types:
            if doc_type not in self.collections:
                logger.warning(f"Unknown document type: {doc_type}")
                continue
            
            collection = self.collections[doc_type]
            
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    include=['documents', 'metadatas', 'distances']
                )
                all_results[doc_type] = results
                
            except Exception as e:
                logger.error(f"Search failed for {doc_type}: {e}")
                all_results[doc_type] = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        return all_results
    
    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics about each collection.
        
        Returns:
            Dictionary with document counts for each collection
        """
        stats = {}
        
        for doc_type, collection in self.collections.items():
            try:
                count = collection.count()
                stats[doc_type] = count
            except Exception as e:
                logger.error(f"Failed to get stats for {doc_type}: {e}")
                stats[doc_type] = 0
        
        return stats
    
    def clear_collection(self, doc_type: str):
        """
        Clear all documents from a specific collection.
        
        Args:
            doc_type: Type of document collection to clear
        """
        if doc_type not in self.collections:
            raise ValueError(f"Unknown document type: {doc_type}")
        
        try:
            # Delete and recreate collection
            self.client.delete_collection(f"{doc_type}_collection_name")
            
            # Recreate with appropriate name
            collection_names = {
                "faq": "company_faq",
                "products": "product_details", 
                "orders": "order_info"
            }
            
            self.collections[doc_type] = self.client.create_collection(
                name=collection_names[doc_type]
            )
            
            logger.info(f"Cleared {doc_type} collection")
            
        except Exception as e:
            logger.error(f"Failed to clear {doc_type} collection: {e}")
            raise
    
    def close(self):
        """Close the ChromaDB client."""
        # ChromaDB client doesn't require explicit closing
        logger.info("ChromaDB connection closed")


# Configuration for different document types
DOCUMENT_CONFIG = {
    "faq": {
        "file_path": "data/documents/faq.pdf",
        "chunk_size": 300,
        "overlap": 50,
        "collection": "company_faq",
        "metadata": {"type": "faq", "category": "support"}
    },
    "products": {
        "file_path": "data/documents/product_details.pdf",
        "chunk_size": 400,
        "overlap": 60,
        "collection": "product_details",
        "metadata": {"type": "product", "category": "features"}
    },
    "orders": {
        "file_path": "data/documents/order_info.pdf",
        "chunk_size": 350,
        "overlap": 50,
        "collection": "order_info",
        "metadata": {"type": "order", "category": "pricing"}
    }
}