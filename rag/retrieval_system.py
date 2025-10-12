"""
Smart Retrieval System for semantic search and context generation.

This module provides intelligent document retrieval by:
- Classifying queries to determine relevant document types
- Performing semantic search across multiple collections
- Ranking and filtering results by relevance
- Formatting context for agent responses
"""

from typing import List, Dict, Optional, Tuple
import logging
import re
from .vector_store import CompanyKnowledgeBase

logger = logging.getLogger(__name__)


class SmartRetriever:
    """
    Intelligent document retrieval system that combines query classification
    with semantic search to provide the most relevant company information.
    """
    
    def __init__(self, knowledge_base: CompanyKnowledgeBase):
        """
        Initialize the smart retriever.
        
        Args:
            knowledge_base: ChromaDB-based knowledge base instance
        """
        self.kb = knowledge_base
        
        # Keywords for classifying queries into document types
        self.query_classifiers = {
            "faq": [
                "how", "what", "why", "when", "where", "help", "problem", "issue", 
                "question", "support", "trouble", "error", "fix", "solve", "guide",
                "tutorial", "instructions", "setup", "configure", "install"
            ],
            "products": [
                "feature", "capability", "product", "solution", "service", "function",
                "specification", "benefit", "advantage", "technology", "system",
                "platform", "tool", "software", "application", "integration"
            ],
            "orders": [
                "price", "cost", "order", "buy", "purchase", "payment", "billing",
                "plan", "package", "subscription", "license", "pricing", "quote",
                "estimate", "budget", "discount", "offer", "deal", "contract"
            ]
        }
        
        # Similarity threshold for filtering results (cosine distance, higher = more permissive)
        self.similarity_threshold = 2.0
        
        logger.info("Smart Retriever initialized")
    
    def classify_query(self, query: str) -> List[str]:
        """
        Determine which document types are most relevant for a query.
        
        Args:
            query: User's search query
            
        Returns:
            List of relevant document types, ordered by relevance
        """
        query_lower = query.lower()
        relevance_scores = {}
        
        # Calculate relevance scores for each document type
        for doc_type, keywords in self.query_classifiers.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    # Exact match gets higher score
                    if f" {keyword} " in f" {query_lower} ":
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                relevance_scores[doc_type] = score
        
        # Sort by relevance score (descending)
        relevant_types = sorted(relevance_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return only the document types (without scores)
        result = [doc_type for doc_type, score in relevant_types]
        
        # If no specific type detected, search all types
        if not result:
            result = list(self.query_classifiers.keys())
        
        logger.debug(f"Query '{query}' classified as relevant to: {result}")
        return result
    
    def retrieve_context(self, query: str, max_context_length: int = 2000, n_results: int = 3) -> str:
        """
        Retrieve and format relevant context for a query.
        
        Args:
            query: User's search query
            max_context_length: Maximum characters in the final context
            n_results: Maximum results per document type
            
        Returns:
            Formatted context string for agent response
        """
        try:
            # Classify query to determine relevant document types
            relevant_types = self.classify_query(query)
            
            # Search across relevant document types
            search_results = self.kb.search_documents(query, relevant_types, n_results)
            
            # Format and combine results
            context_parts = self._format_search_results(search_results, max_context_length)
            
            if not context_parts:
                logger.warning(f"No relevant context found for query: {query}")
                return ""
            
            # Join all context parts
            final_context = "\n\n".join(context_parts)
            
            logger.info(f"Retrieved context for '{query}': {len(final_context)} characters")
            return final_context
            
        except Exception as e:
            logger.error(f"Context retrieval failed for query '{query}': {e}")
            return ""
    
    def _format_search_results(self, search_results: Dict, max_length: int) -> List[str]:
        """
        Format search results into context strings.
        
        Args:
            search_results: Dictionary of search results by document type
            max_length: Maximum total length of formatted results
            
        Returns:
            List of formatted context strings
        """
        context_parts = []
        current_length = 0
        
        # Process results by document type priority
        for doc_type in ["orders", "products", "faq"]:  # Priority order
            if doc_type not in search_results:
                continue
            
            results = search_results[doc_type]
            
            # Skip if no results
            if not results.get('documents') or not results['documents'][0]:
                continue
            
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(documents)
            distances = results['distances'][0] if results.get('distances') else [0.0] * len(documents)
            
            # Process each document result
            for doc, metadata, distance in zip(documents, metadatas, distances):
                # Skip if similarity is too low (higher distance = lower similarity)
                if distance > self.similarity_threshold:
                    continue
                
                # Check if adding this would exceed max length
                estimated_addition = len(doc) + 50  # 50 for formatting
                if current_length + estimated_addition > max_length:
                    break
                
                # Format the context entry
                formatted_entry = self._format_context_entry(doc_type, doc, metadata, distance)
                
                if formatted_entry:
                    context_parts.append(formatted_entry)
                    current_length += len(formatted_entry)
            
            # Stop if we've reached the max length
            if current_length >= max_length * 0.9:  # 90% threshold
                break
        
        return context_parts
    
    def _format_context_entry(self, doc_type: str, document: str, metadata: Dict, distance: float) -> str:
        """
        Format a single context entry.
        
        Args:
            doc_type: Type of document
            document: Document text
            metadata: Document metadata
            distance: Similarity distance (lower = more similar)
            
        Returns:
            Formatted context entry
        """
        # Clean up the document text
        clean_doc = document.strip()
        
        # Truncate if too long
        if len(clean_doc) > 800:
            clean_doc = clean_doc[:800] + "..."
        
        # Format with document type label
        doc_type_labels = {
            "faq": "FAQ",
            "products": "PRODUCT INFO",
            "orders": "PRICING & ORDERS"
        }
        
        label = doc_type_labels.get(doc_type, doc_type.upper())
        
        # Calculate confidence percentage
        confidence = int((1.0 - distance) * 100)
        
        return f"[{label}] {clean_doc}"
    
    def search_specific_type(self, query: str, doc_type: str, n_results: int = 5) -> List[Dict]:
        """
        Search within a specific document type.
        
        Args:
            query: Search query
            doc_type: Specific document type to search
            n_results: Maximum number of results
            
        Returns:
            List of search results with metadata
        """
        try:
            search_results = self.kb.search_documents(query, [doc_type], n_results)
            
            if doc_type not in search_results:
                return []
            
            results = search_results[doc_type]
            
            if not results.get('documents') or not results['documents'][0]:
                return []
            
            # Combine results with metadata
            formatted_results = []
            
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    "text": doc,
                    "metadata": results['metadatas'][0][i] if results.get('metadatas') else {},
                    "similarity": 1.0 - results['distances'][0][i] if results.get('distances') else 1.0,
                    "document_type": doc_type
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Specific search failed for {doc_type}: {e}")
            return []
    
    def get_retrieval_stats(self) -> Dict[str, any]:
        """
        Get statistics about the retrieval system.
        
        Returns:
            Dictionary with retrieval system statistics
        """
        try:
            kb_stats = self.kb.get_collection_stats()
            
            return {
                "total_documents": sum(kb_stats.values()),
                "collections": kb_stats,
                "similarity_threshold": self.similarity_threshold,
                "query_classifiers": {k: len(v) for k, v in self.query_classifiers.items()}
            }
            
        except Exception as e:
            logger.error(f"Failed to get retrieval stats: {e}")
            return {}
    
    def update_similarity_threshold(self, threshold: float):
        """
        Update the similarity threshold for filtering results.
        
        Args:
            threshold: New similarity threshold (0.0 to 1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold = threshold
            logger.info(f"Updated similarity threshold to {threshold}")
        else:
            logger.warning(f"Invalid similarity threshold: {threshold}")


# Utility functions for common retrieval operations

def quick_search(knowledge_base: CompanyKnowledgeBase, query: str) -> str:
    """
    Quick search utility function.
    
    Args:
        knowledge_base: ChromaDB knowledge base
        query: Search query
        
    Returns:
        Formatted context string
    """
    retriever = SmartRetriever(knowledge_base)
    return retriever.retrieve_context(query)


def search_pricing_info(knowledge_base: CompanyKnowledgeBase, query: str) -> List[Dict]:
    """
    Search specifically for pricing and order information.
    
    Args:
        knowledge_base: ChromaDB knowledge base
        query: Pricing-related query
        
    Returns:
        List of pricing-related results
    """
    retriever = SmartRetriever(knowledge_base)
    return retriever.search_specific_type(query, "orders")


def search_product_features(knowledge_base: CompanyKnowledgeBase, query: str) -> List[Dict]:
    """
    Search specifically for product features and capabilities.
    
    Args:
        knowledge_base: ChromaDB knowledge base
        query: Product-related query
        
    Returns:
        List of product-related results
    """
    retriever = SmartRetriever(knowledge_base)
    return retriever.search_specific_type(query, "products")


def search_support_info(knowledge_base: CompanyKnowledgeBase, query: str) -> List[Dict]:
    """
    Search specifically for FAQ and support information.
    
    Args:
        knowledge_base: ChromaDB knowledge base
        query: Support-related query
        
    Returns:
        List of support-related results
    """
    retriever = SmartRetriever(knowledge_base)
    return retriever.search_specific_type(query, "faq")