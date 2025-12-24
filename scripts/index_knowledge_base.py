"""
Offline knowledge base indexing pipeline.

This script prepares the knowledge base for runtime usage by loading source
documents, processing them, and creating a searchable vector index.

Note: Run this script manually whenever you update the knowledge base documents.
"""

import logging
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from services.knowledge_base import KnowledgeBase
from services.knowledge_base.sources import PdfTextSource
from services.knowledge_base.stores import ChromaVectorStore

# ============================================================================
# CONFIGURATION - Edit these values to customize indexing behavior
# ============================================================================

# Path to the PDF document containing your knowledge base
PDF_SOURCE_PATH = "data/knowledge_base.pdf"

# Vector database storage location
VECTOR_STORE_PATH = "./data/chroma/"

# Collection name in the vector database
COLLECTION_NAME = "company_knowledge"

# OpenAI API configuration for embeddings
OPENAI_API_KEY = "YOUR_OPENAI_KEY"  # Replace with your actual API key
EMBEDDING_MODEL = "text-embedding-3-small"

# Text chunking parameters
CHUNK_SIZE = 500        # Number of characters per chunk
CHUNK_OVERLAP = 50      # Overlap between consecutive chunks

# Set to True to delete existing index before rebuilding
CLEAR_EXISTING_INDEX = False


# ============================================================================
# Logging setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Initialize components
# ============================================================================

# Set up the PDF source
pdf_source = PdfTextSource(PDF_SOURCE_PATH)

# Configure Chroma vector database client
chroma_client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)

# Configure OpenAI embedding function
embedding_function = OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name=EMBEDDING_MODEL
)

# Get or create the collection
chroma_collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function 
)

# Initialize vector store wrapper
chroma_store = ChromaVectorStore(chroma_collection)


# ============================================================================
# Indexing pipeline
# ============================================================================

def run_indexing_pipeline() -> None:
    """
    Execute the complete indexing pipeline.
    
    Steps:
    1. Verify source document exists
    2. Initialize knowledge base service
    3. Optionally clear existing index
    4. Build and persist new index
    """
    logger.info("Starting knowledge base indexing pipeline")

    # Check if source PDF exists
    if not pdf_source.exists():
        logger.error(f"Source document not found: {PDF_SOURCE_PATH}")
        logger.error("Please check the file path and try again")
        return

    # Initialize knowledge base with configured parameters
    knowledge_base = KnowledgeBase(
        source=pdf_source,
        store=chroma_store,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    # Clear existing data if requested
    if CLEAR_EXISTING_INDEX:
        logger.info("Clearing existing index")
        knowledge_base.clear()

    # Build the searchable index
    logger.info("Building index from source document...")
    chunks_indexed = knowledge_base.build_index()

    # Report results
    logger.info("Indexing completed successfully")
    logger.info(f"Total chunks indexed: {chunks_indexed}")


# ============================================================================
# Script entry point
# ============================================================================

if __name__ == "__main__":
    run_indexing_pipeline()
