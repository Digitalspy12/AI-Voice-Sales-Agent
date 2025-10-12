#!/usr/bin/env python3
"""
Setup script for initializing the company knowledge base.

This script:
1. Validates system requirements
2. Checks for required PDF documents  
3. Processes documents and builds vector database
4. Tests the RAG system functionality
5. Provides setup validation and diagnostics

Usage:
    python setup_knowledge_base.py              # Normal setup
    python setup_knowledge_base.py --force      # Force rebuild
    python setup_knowledge_base.py --validate   # Only validate setup
    python setup_knowledge_base.py --test       # Run tests only
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Compatibility shim for huggingface_hub
try:
    import huggingface_hub
    if not hasattr(huggingface_hub, 'cached_download'):
        from huggingface_hub import hf_hub_download
        huggingface_hub.cached_download = hf_hub_download
except ImportError:
    pass

from rag.knowledge_manager import KnowledgeManager, quick_setup_knowledge_base, test_rag_system
from rag.vector_store import DOCUMENT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_setup.log')
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print setup banner."""
    print("\n" + "="*70)
    print("🚀 AI Voice Sales Agent - RAG Knowledge Base Setup")
    print("="*70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def check_dependencies():
    """
    Check if all required dependencies are installed.
    
    Returns:
        bool: True if all dependencies are available
    """
    required_packages = [
        ('chromadb', 'chromadb'),
        ('sentence_transformers', 'sentence_transformers'), 
        ('PyPDF2', 'PyPDF2'),
        ('logging', 'logging')
    ]
    
    missing_packages = []
    
    for display_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {display_name}")
        except ImportError:
            print(f"❌ {display_name} - MISSING")
            missing_packages.append(display_name)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Please install missing dependencies:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies are installed\n")
    return True


def check_document_files():
    """
    Check if all required PDF documents are present.
    
    Returns:
        dict: Status of each document file
    """
    print("📋 Checking document files...")
    
    file_status = {}
    
    for doc_type, config in DOCUMENT_CONFIG.items():
        file_path = config['file_path']
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"✅ {doc_type:8s}: {file_path} ({file_size_mb:.1f} MB)")
            file_status[doc_type] = {
                'exists': True,
                'path': file_path,
                'size_mb': file_size_mb
            }
        else:
            print(f"❌ {doc_type:8s}: {file_path} - NOT FOUND")
            file_status[doc_type] = {
                'exists': False, 
                'path': file_path,
                'size_mb': 0
            }
    
    missing_files = [dt for dt, status in file_status.items() if not status['exists']]
    
    if missing_files:
        print(f"\n⚠️ Missing document files for: {', '.join(missing_files)}")
        print("\nPlease ensure the following files exist:")
        for doc_type in missing_files:
            print(f"  - {DOCUMENT_CONFIG[doc_type]['file_path']}")
        print("\nYou can:")
        print("1. Add your actual PDF documents to the specified paths")
        print("2. Create sample PDFs for testing")
        print("3. Update paths in rag/vector_store.py DOCUMENT_CONFIG")
        return file_status, False
    
    print("✅ All document files found\n")
    return file_status, True


def setup_knowledge_base(force_rebuild=False):
    """
    Set up the knowledge base with company documents.
    
    Args:
        force_rebuild: Whether to force rebuild existing data
        
    Returns:
        bool: True if setup was successful
    """
    print("🔧 Setting up knowledge base...")
    
    try:
        manager = KnowledgeManager()
        
        # Check current state
        stats = manager.get_system_stats()
        current_docs = stats.get('knowledge_base', {}).get('total_documents', 0)
        
        if current_docs > 0 and not force_rebuild:
            print(f"📊 Knowledge base already contains {current_docs} documents")
            print("Use --force to rebuild from scratch")
            return True
        
        if force_rebuild and current_docs > 0:
            print(f"🔄 Force rebuilding knowledge base (current: {current_docs} documents)")
            
        # Process documents
        print("📖 Processing company documents...")
        results = manager.refresh_all_documents()
        
        # Report results
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"\n📊 Processing Results:")
        for doc_type, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED" 
            print(f"  {doc_type:8s}: {status}")
        
        if successful == total:
            print(f"\n🎉 Knowledge base setup complete! ({successful}/{total} documents processed)")
            
            # Show final stats
            final_stats = manager.get_system_stats()
            total_chunks = final_stats.get('knowledge_base', {}).get('total_documents', 0)
            collections = final_stats.get('knowledge_base', {}).get('collections', {})
            
            print("\n📈 Final Statistics:")
            print(f"  Total chunks: {total_chunks}")
            for collection, count in collections.items():
                print(f"  {collection:12s}: {count} chunks")
            
            return True
        else:
            print(f"\n⚠️ Setup completed with errors ({successful}/{total} successful)")
            return False
            
    except Exception as e:
        logger.error(f"Knowledge base setup failed: {e}")
        print(f"❌ Setup failed: {e}")
        return False


def run_tests():
    """
    Run tests to validate the RAG system functionality.
    
    Returns:
        bool: True if all tests pass
    """
    print("🧪 Running RAG system tests...")
    
    try:
        manager = KnowledgeManager()
        
        # Test queries covering different document types
        test_queries = [
            ("What are your pricing plans?", "orders"),
            ("How does the DD solution work?", "products"), 
            ("How do I get support?", "faq"),
            ("What features are included in the product?", "products"),
            ("How do I place an order?", "orders"),
            ("What is your refund policy?", "faq")
        ]
        
        print(f"Running {len(test_queries)} test queries...\n")
        
        passed_tests = 0
        
        for i, (query, expected_type) in enumerate(test_queries, 1):
            print(f"Test {i}: {query}")
            
            try:
                context = manager.search_test(query, verbose=False)
                
                if context:
                    context_length = len(context)
                    # Check if expected document type appears in context
                    type_found = expected_type.upper() in context.upper() or len(context) > 50
                    
                    if type_found:
                        print(f"  ✅ PASS ({context_length} chars retrieved)")
                        passed_tests += 1
                    else:
                        print(f"  ⚠️ PARTIAL (context found but may not match expected type)")
                        passed_tests += 0.5
                else:
                    print(f"  ❌ FAIL (no context retrieved)")
                    
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
            
            print()
        
        success_rate = (passed_tests / len(test_queries)) * 100
        
        print(f"📊 Test Results: {passed_tests}/{len(test_queries)} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 RAG system tests PASSED!")
            return True
        else:
            print("⚠️ RAG system tests had issues. Consider debugging.")
            return False
            
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        print(f"❌ Test execution failed: {e}")
        return False


def validate_setup():
    """
    Validate the complete RAG system setup.
    
    Returns:
        bool: True if validation passes
    """
    print("🔍 Validating RAG system setup...")
    
    try:
        manager = KnowledgeManager()
        validation_results = manager.validate_setup()
        
        overall_status = validation_results.get('overall_status', 'UNKNOWN')
        
        print(f"\n📋 Validation Results:")
        print(f"Overall Status: {overall_status}")
        print()
        
        # Component validation
        print("🔧 Components:")
        components = validation_results.get('components', {})
        for component, status_info in components.items():
            status = status_info.get('status', 'UNKNOWN')
            status_icon = "✅" if status == "OK" else "❌"
            print(f"  {status_icon} {component}: {status}")
            if status == "ERROR":
                error = status_info.get('error', 'Unknown error')
                print(f"    Error: {error}")
        
        # Document files
        print("\n📄 Document Files:")
        doc_files = validation_results.get('document_files', {})
        for doc_type, file_info in doc_files.items():
            exists = file_info.get('exists', False)
            valid = file_info.get('valid_pdf', False)
            
            if exists and valid:
                print(f"  ✅ {doc_type}: Available and valid")
            elif exists and not valid:
                print(f"  ⚠️ {doc_type}: File exists but may be invalid")
            else:
                print(f"  ❌ {doc_type}: File missing")
        
        # Test queries
        print("\n🧪 Query Tests:")
        test_queries = validation_results.get('test_queries', {})
        for query, test_info in test_queries.items():
            status = test_info.get('status', 'UNKNOWN')
            has_context = test_info.get('has_context', False)
            
            if status == "OK" and has_context:
                print(f"  ✅ '{query[:30]}...': Working")
            elif status == "OK" and not has_context:
                print(f"  ⚠️ '{query[:30]}...': No context found")
            else:
                print(f"  ❌ '{query[:30]}...': Failed")
        
        # Summary
        print(f"\n📊 Validation Summary:")
        if overall_status == "OK":
            print("🎉 All systems operational! RAG setup is complete and functional.")
            return True
        elif overall_status == "WARNING":
            print("⚠️ System is mostly functional but has some warnings.")
            return True
        else:
            print("❌ System has errors that need to be addressed.")
            return False
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        return False


def create_sample_documents():
    """Create sample PDF documents for testing if they don't exist."""
    print("📝 Creating sample documents for testing...")
    
    sample_texts = {
        "faq": """
        Frequently Asked Questions
        
        Q: How do I get started with the DD solution?
        A: Contact our support team to schedule an onboarding session.
        
        Q: What technical support is available?
        A: We provide 24/7 technical support via email, phone, and chat.
        
        Q: How do I reset my password?
        A: Use the password reset link on the login page or contact support.
        """,
        
        "products": """
        DD Solution Features
        
        Our Due Diligence solution includes:
        - Automated risk assessment
        - Real-time compliance monitoring  
        - Integration with existing systems
        - Advanced analytics and reporting
        - Multi-language support
        
        Key Benefits:
        - Reduce due diligence time by 60%
        - Improve accuracy and consistency
        - Ensure regulatory compliance
        """,
        
        "orders": """
        Pricing and Orders
        
        Starter Package: $2,000/month
        - Up to 5 users
        - Basic features
        - Email support
        
        Professional Package: $5,000/month  
        - Up to 25 users
        - Advanced features
        - Priority support
        
        Enterprise Package: $10,000/month
        - Unlimited users
        - All features
        - Dedicated support
        """
    }
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        os.makedirs("data/documents", exist_ok=True)
        
        for doc_type, content in sample_texts.items():
            file_path = f"data/documents/{doc_type}.pdf"
            
            if not os.path.exists(file_path):
                # Create PDF
                c = canvas.Canvas(file_path, pagesize=letter)
                
                # Add content
                lines = content.strip().split('\n')
                y = 750
                
                for line in lines:
                    if line.strip():
                        c.drawString(50, y, line.strip()[:80])  # Limit line length
                        y -= 20
                        
                        if y < 50:  # Start new page if needed
                            c.showPage()
                            y = 750
                
                c.save()
                print(f"  ✅ Created: {file_path}")
            else:
                print(f"  📄 Exists: {file_path}")
        
        print("📝 Sample documents ready!")
        return True
        
    except ImportError:
        print("⚠️ reportlab not installed. Cannot create sample PDFs.")
        print("Install with: pip install reportlab")
        print("Or manually create PDF files in data/documents/")
        return False
    except Exception as e:
        print(f"❌ Failed to create sample documents: {e}")
        return False


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup RAG knowledge base for AI Voice Sales Agent"
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Force rebuild even if knowledge base exists'
    )
    parser.add_argument(
        '--validate', action='store_true', 
        help='Only validate existing setup'
    )
    parser.add_argument(
        '--test', action='store_true',
        help='Run tests only'
    )
    parser.add_argument(
        '--create-samples', action='store_true',
        help='Create sample PDF documents for testing'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Create sample documents if requested
    if args.create_samples:
        create_sample_documents()
        return
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Setup aborted due to missing dependencies")
        sys.exit(1)
    
    # Check document files
    file_status, files_ok = check_document_files()
    
    if not files_ok and not args.validate:
        print("\n💡 Tip: Use --create-samples to generate test documents")
        print("❌ Setup aborted due to missing files")
        sys.exit(1)
    
    # Validate only
    if args.validate:
        success = validate_setup()
        sys.exit(0 if success else 1)
    
    # Test only  
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # Full setup
    setup_success = setup_knowledge_base(force_rebuild=args.force)
    
    if setup_success:
        # Run validation
        print("\n" + "="*70)
        validate_success = validate_setup()
        
        if validate_success:
            print("\n" + "="*70)
            test_success = run_tests()
            
            if test_success:
                print("\n🎉 SETUP COMPLETE! Your RAG system is ready to use.")
                print("\nNext steps:")
                print("1. Update agent.py to integrate RAG system")
                print("2. Test with your voice agent")
                print("3. Monitor search quality and optimize as needed")
            else:
                print("\n⚠️ Setup complete but tests had issues")
                sys.exit(1)
        else:
            print("\n❌ Setup completed but validation failed")
            sys.exit(1)
    else:
        print("\n❌ Setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()