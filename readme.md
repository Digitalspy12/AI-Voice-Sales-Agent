## If error related Venv
- Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

## To run 
-  .\venv\Scripts\activate
- python agent.py console 


# Test if dependencies are installed correctly
python -c "import chromadb, sentence_transformers, PyPDF2; print('✅ All RAG dependencies installed')"

# First, let's install reportlab for PDF creation
pip install reportlab

# Create sample PDF documents
python setup_knowledge_base.py --create-samples
# Run the complete setup
python setup_knowledge_base.py
# Validate the system
python setup_knowledge_base.py --validate
# Test with sample queries
python setup_knowledge_base.py --test
# Backup your current agent
cp agent.py agent_backup.py

# Use the RAG-enhanced agent
cp agent_with_rag_example.py agent.py

## Set up .env

LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=


GOOGLE_API_KEY=


