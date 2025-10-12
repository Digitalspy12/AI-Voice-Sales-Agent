"""
Knowledge Manager for document management and setup utilities.

This module provides high-level utilities for:
- Adding new documents to the knowledge base
- Refreshing existing documents
- Managing different document categories
- Testing search functionality
- System maintenance operations
"""

from typing import Dict, List, Optional
import logging
import os
from datetime import datetime

from .document_processor import DocumentProcessor
from .vector_store import CompanyKnowledgeBase, DOCUMENT_CONFIG
from .retrieval_system import SmartRetriever

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    High-level manager for company knowledge base operations.
    
    Provides utilities for document management, search testing,
    and system maintenance.
    """
    
    def __init__(self, chroma_db_path: str = "./chroma_db"):
        """
        Initialize the knowledge manager.
        
        Args:
            chroma_db_path: Path to ChromaDB storage directory
        """
        try:
            # Initialize components
            self.processor = DocumentProcessor()
            self.knowledge_base = CompanyKnowledgeBase(chroma_db_path)
            self.retriever = SmartRetriever(self.knowledge_base)
            
            logger.info("Knowledge Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Knowledge Manager: {e}")
            raise
    
    def add_document(self, file_path: str, doc_type: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add a new document to the knowledge base.
        
        Args:
            file_path: Path to the PDF file
            doc_type: Type of document ('faq', 'products', 'orders')
            metadata: Additional metadata for the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            if doc_type not in ['faq', 'products', 'orders']:
                logger.error(f"Invalid document type: {doc_type}")
                return False
            
            # Validate PDF
            if not self.processor.validate_pdf(file_path):
                logger.error(f"Invalid PDF file: {file_path}")
                return False
            
            logger.info(f"Processing document: {file_path} as {doc_type}")
            
            # Get configuration for this document type
            config = DOCUMENT_CONFIG.get(doc_type, {})
            chunk_size = config.get('chunk_size', 400)
            overlap = config.get('overlap', 50)
            
            # Process the document
            chunks, embeddings = self.processor.process_document(
                file_path, 
                chunk_size=chunk_size, 
                overlap=overlap
            )
            
            if not chunks:
                logger.error(f"No chunks generated from {file_path}")
                return False
            
            # Add metadata to chunks
            base_metadata = config.get('metadata', {})
            if metadata:
                base_metadata.update(metadata)
            
            # Add source file info
            base_metadata.update({
                "source_file": os.path.basename(file_path),
                "file_path": file_path,
                "processed_at": datetime.now().isoformat()
            })
            
            for chunk in chunks:
                chunk.update(base_metadata)
            
            # Store in knowledge base
            self.knowledge_base.store_documents(doc_type, chunks, embeddings)
            
            logger.info(f"Successfully added {len(chunks)} chunks from {file_path} to {doc_type} collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document {file_path}: {e}")
            return False
    
    def refresh_all_documents(self) -> Dict[str, bool]:
        """
        Refresh all company documents from the configured paths.
        
        Returns:
            Dictionary with success status for each document type
        """
        results = {}
        
        for doc_type, config in DOCUMENT_CONFIG.items():
            file_path = config['file_path']
            
            try:
                if os.path.exists(file_path):
                    logger.info(f"Refreshing {doc_type} from {file_path}")
                    
                    # Clear existing documents of this type
                    # (Optional: you might want to keep existing data)
                    # self.knowledge_base.clear_collection(doc_type)
                    
                    # Add the document
                    success = self.add_document(file_path, doc_type, config.get('metadata', {}))
                    results[doc_type] = success
                    
                else:
                    logger.warning(f"Document file not found: {file_path}")
                    results[doc_type] = False
                    
            except Exception as e:
                logger.error(f"Failed to refresh {doc_type}: {e}")
                results[doc_type] = False
        
        # Log summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"Document refresh complete: {successful}/{total} successful")
        
        return results
    
    def search_test(self, query: str, verbose: bool = True) -> str:
        """
        Test search functionality with a query.
        
        Args:
            query: Search query to test
            verbose: Whether to print detailed results
            
        Returns:
            Retrieved context string
        """
        try:
            # Perform search
            context = self.retriever.retrieve_context(query)
            
            if verbose:
                print(f"\n{'='*60}")
                print(f"SEARCH TEST")
                print(f"{'='*60}")
                print(f"Query: {query}")
                print(f"{'='*60}")
                
                if context:
                    print(f"Retrieved Context ({len(context)} chars):")
                    print(f"{'-'*40}")
                    print(context)
                else:
                    print("No relevant context found.")
                
                print(f"{'='*60}\n")
            
            return context
            
        except Exception as e:
            logger.error(f"Search test failed for query '{query}': {e}")
            return ""
    
    def get_system_stats(self) -> Dict:
        """
        Get comprehensive system statistics.
        
        Returns:
            Dictionary with system statistics
        """
        try:
            # Get knowledge base stats
            kb_stats = self.knowledge_base.get_collection_stats()
            
            # Get retrieval stats
            retrieval_stats = self.retriever.get_retrieval_stats()
            
            # Get processor info
            processor_info = self.processor.get_model_info()
            
            # Compile system stats
            system_stats = {
                "timestamp": datetime.now().isoformat(),
                "knowledge_base": {
                    "collections": kb_stats,
                    "total_documents": sum(kb_stats.values()),
                    "database_path": self.knowledge_base.persist_directory
                },
                "retrieval_system": retrieval_stats,
                "document_processor": processor_info,
                "configuration": DOCUMENT_CONFIG
            }
            
            return system_stats
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def validate_setup(self) -> Dict[str, any]:
        """
        Validate the complete RAG system setup.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "overall_status": "UNKNOWN",
            "components": {},
            "document_files": {},
            "test_queries": {}
        }
        
        try:
            # Test document processor
            try:
                model_info = self.processor.get_model_info()
                validation_results["components"]["document_processor"] = {
                    "status": "OK",
                    "details": model_info
                }
            except Exception as e:
                validation_results["components"]["document_processor"] = {
                    "status": "ERROR",
                    "error": str(e)
                }
            
            # Test knowledge base
            try:
                kb_stats = self.knowledge_base.get_collection_stats()
                validation_results["components"]["knowledge_base"] = {
                    "status": "OK",
                    "collections": kb_stats
                }
            except Exception as e:
                validation_results["components"]["knowledge_base"] = {
                    "status": "ERROR",
                    "error": str(e)
                }
            
            # Test retrieval system
            try:
                retrieval_stats = self.retriever.get_retrieval_stats()
                validation_results["components"]["retrieval_system"] = {
                    "status": "OK",
                    "stats": retrieval_stats
                }
            except Exception as e:
                validation_results["components"]["retrieval_system"] = {
                    "status": "ERROR",
                    "error": str(e)
                }
            
            # Check document files
            for doc_type, config in DOCUMENT_CONFIG.items():
                file_path = config['file_path']
                if os.path.exists(file_path):
                    is_valid = self.processor.validate_pdf(file_path)
                    validation_results["document_files"][doc_type] = {
                        "file_path": file_path,
                        "exists": True,
                        "valid_pdf": is_valid
                    }
                else:
                    validation_results["document_files"][doc_type] = {
                        "file_path": file_path,
                        "exists": False,
                        "valid_pdf": False
                    }
            
            # Test with sample queries
            test_queries = [
                "What are your pricing plans?",
                "How does the product work?",
                "How do I get support?"
            ]
            
            for query in test_queries:
                try:
                    context = self.retriever.retrieve_context(query, max_context_length=500)
                    validation_results["test_queries"][query] = {
                        "status": "OK",
                        "context_length": len(context),
                        "has_context": len(context) > 0
                    }
                except Exception as e:
                    validation_results["test_queries"][query] = {
                        "status": "ERROR",
                        "error": str(e)
                    }
            
            # Determine overall status
            component_errors = [c for c in validation_results["components"].values() if c["status"] == "ERROR"]
            missing_files = [f for f in validation_results["document_files"].values() if not f["exists"]]
            query_errors = [q for q in validation_results["test_queries"].values() if q["status"] == "ERROR"]
            
            if component_errors:
                validation_results["overall_status"] = "ERROR"
            elif missing_files:
                validation_results["overall_status"] = "WARNING"
            elif query_errors:
                validation_results["overall_status"] = "WARNING"
            else:
                validation_results["overall_status"] = "OK"
            
            return validation_results
            
        except Exception as e:
            logger.error(f"System validation failed: {e}")
            validation_results["overall_status"] = "ERROR"
            validation_results["validation_error"] = str(e)
            return validation_results
    
    def maintenance_mode(self, operation: str) -> bool:
        """
        Perform system maintenance operations.
        
        Args:
            operation: Maintenance operation ('clear_all', 'rebuild', 'optimize')
            
        Returns:
            True if successful
        """
        try:
            if operation == "clear_all":
                logger.info("Clearing all collections...")
                for doc_type in ['faq', 'products', 'orders']:
                    self.knowledge_base.clear_collection(doc_type)
                logger.info("All collections cleared")
                return True
            
            elif operation == "rebuild":
                logger.info("Rebuilding knowledge base from documents...")
                self.maintenance_mode("clear_all")
                results = self.refresh_all_documents()
                success = all(results.values())
                if success:
                    logger.info("Knowledge base rebuild complete")
                else:
                    logger.warning("Knowledge base rebuild completed with some errors")
                return success
            
            elif operation == "optimize":
                logger.info("Optimizing knowledge base...")
                # Future: implement optimization logic
                # For now, just rebuild
                return self.maintenance_mode("rebuild")
            
            else:
                logger.error(f"Unknown maintenance operation: {operation}")
                return False
                
        except Exception as e:
            logger.error(f"Maintenance operation '{operation}' failed: {e}")
            return False
    
    def close(self):
        """Close the knowledge manager and cleanup resources."""
        try:
            self.knowledge_base.close()
            logger.info("Knowledge Manager closed")
        except Exception as e:
            logger.error(f"Error closing Knowledge Manager: {e}")


# Utility functions for quick operations

def quick_setup_knowledge_base(force_rebuild: bool = False) -> bool:
    """
    Quick utility to set up the knowledge base.
    
    Args:
        force_rebuild: Whether to rebuild even if data exists
        
    Returns:
        True if successful
    """
    try:
        manager = KnowledgeManager()
        
        # Check if we need to build
        stats = manager.get_system_stats()
        total_docs = stats.get("knowledge_base", {}).get("total_documents", 0)
        
        if total_docs == 0 or force_rebuild:
            logger.info("Setting up knowledge base...")
            results = manager.refresh_all_documents()
            success = all(results.values())
            
            if success:
                logger.info("✅ Knowledge base setup complete!")
            else:
                logger.warning("⚠️ Knowledge base setup completed with some errors")
                
            return success
        else:
            logger.info(f"Knowledge base already contains {total_docs} documents")
            return True
            
    except Exception as e:
        logger.error(f"Quick setup failed: {e}")
        return False


def test_rag_system(queries: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Quick utility to test the RAG system with sample queries.
    
    Args:
        queries: List of test queries (uses defaults if None)
        
    Returns:
        Dictionary mapping queries to retrieved contexts
    """
    if queries is None:
        queries = [
            "What are your pricing plans?",
            "How does the DD solution work?", 
            "How do I get support?",
            "What features are included?",
            "How do I place an order?"
        ]
    
    try:
        manager = KnowledgeManager()
        results = {}
        
        for query in queries:
            context = manager.search_test(query, verbose=False)
            results[query] = context
        
        return results
        
    except Exception as e:
        logger.error(f"RAG system test failed: {e}")
        return {}