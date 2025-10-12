"""
Document Processing module for PDF parsing and text chunking.

This module handles:
- PDF text extraction from company documents
- Intelligent text chunking with overlap
- Embedding generation using sentence transformers
- Text preprocessing and cleaning
"""

import PyPDF2
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
import logging
import re
import os

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes PDF documents into chunks suitable for vector storage.
    
    Features:
    - PDF text extraction with error handling
    - Intelligent text chunking with overlap
    - Embedding generation using pre-trained models
    - Text cleaning and preprocessing
    """
    
    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the document processor.
        
        Args:
            embedding_model: HuggingFace model name for embeddings
        """
        self.embedding_model_name = embedding_model
        
        try:
            # Load the embedding model
            self.embedder = SentenceTransformer(embedding_model)
            logger.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {embedding_model}: {e}")
            raise
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF extraction fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            text = ""
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                logger.info(f"Processing PDF with {len(reader.pages)} pages: {pdf_path}")
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():  # Only add non-empty pages
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                        continue
            
            if not text.strip():
                raise ValueError(f"No text could be extracted from {pdf_path}")
            
            # Clean the extracted text
            cleaned_text = self._clean_text(text)
            
            logger.info(f"Extracted {len(cleaned_text)} characters from {pdf_path}")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {pdf_path}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and preprocess extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers patterns (customize based on your PDFs)
        text = re.sub(r'--- Page \d+ ---', '', text)
        
        # Fix common OCR errors
        text = text.replace('', '')  # Remove null characters
        text = text.replace('\x00', '')  # Remove null bytes
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove excessive line breaks
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """
        Split text into overlapping chunks with metadata.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum words per chunk
            overlap: Number of overlapping words between chunks
            
        Returns:
            List of dictionaries containing chunk text and metadata
        """
        if not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        words = text.split()
        chunks = []
        
        if len(words) <= chunk_size:
            # If text is smaller than chunk size, return as single chunk
            chunks.append({
                "text": text.strip(),
                "chunk_id": "chunk_0",
                "start_index": 0,
                "end_index": len(words),
                "word_count": len(words),
                "chunk_number": 0
            })
            return chunks
        
        chunk_number = 0
        
        for i in range(0, len(words), chunk_size - overlap):
            # Calculate chunk boundaries
            start_idx = i
            end_idx = min(i + chunk_size, len(words))
            
            # Extract chunk words
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)
            
            # Create chunk metadata
            chunk_data = {
                "text": chunk_text.strip(),
                "chunk_id": f"chunk_{chunk_number}",
                "start_index": start_idx,
                "end_index": end_idx,
                "word_count": len(chunk_words),
                "chunk_number": chunk_number
            }
            
            chunks.append(chunk_data)
            chunk_number += 1
            
            # Break if we've reached the end
            if end_idx >= len(words):
                break
        
        logger.info(f"Created {len(chunks)} chunks from {len(words)} words")
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (list of floats)
        """
        if not texts:
            logger.warning("Empty text list provided for embedding generation")
            return []
        
        try:
            # Generate embeddings using sentence transformer
            embeddings = self.embedder.encode(texts, convert_to_numpy=True)
            
            # Convert to list format for ChromaDB
            embedding_lists = embeddings.tolist()
            
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embedding_lists
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def process_document(self, pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> Tuple[List[Dict], List[List[float]]]:
        """
        Complete document processing pipeline.
        
        Args:
            pdf_path: Path to PDF file
            chunk_size: Maximum words per chunk
            overlap: Number of overlapping words
            
        Returns:
            Tuple of (chunks, embeddings)
        """
        try:
            # Extract text from PDF
            text = self.extract_pdf_text(pdf_path)
            
            # Create chunks
            chunks = self.chunk_text(text, chunk_size, overlap)
            
            if not chunks:
                raise ValueError(f"No chunks created from {pdf_path}")
            
            # Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.generate_embeddings(chunk_texts)
            
            logger.info(f"Successfully processed {pdf_path}: {len(chunks)} chunks with embeddings")
            return chunks, embeddings
            
        except Exception as e:
            logger.error(f"Document processing failed for {pdf_path}: {e}")
            raise
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Validate if a PDF file can be processed.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF is valid and readable
        """
        try:
            if not os.path.exists(pdf_path):
                return False
            
            # Try to read the PDF
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Check if we can access pages
                if len(reader.pages) == 0:
                    return False
                
                # Try to extract text from first page
                first_page_text = reader.pages[0].extract_text()
                
                return True
                
        except Exception as e:
            logger.warning(f"PDF validation failed for {pdf_path}: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the embedding model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.embedding_model_name,
            "embedding_dimension": str(self.embedder.get_sentence_embedding_dimension()),
            "max_sequence_length": str(self.embedder.max_seq_length)
        }


# Utility function for quick document processing
def quick_process_pdf(pdf_path: str, doc_type: str = "unknown") -> Tuple[List[Dict], List[List[float]]]:
    """
    Quick utility to process a PDF with default settings.
    
    Args:
        pdf_path: Path to PDF file
        doc_type: Type of document for metadata
        
    Returns:
        Tuple of (chunks, embeddings)
    """
    processor = DocumentProcessor()
    chunks, embeddings = processor.process_document(pdf_path)
    
    # Add document type to metadata
    for chunk in chunks:
        chunk["document_type"] = doc_type
    
    return chunks, embeddings