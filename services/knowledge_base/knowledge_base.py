"""
Knowledge Base Service
"""
import logging
from typing import Iterable, List, Dict, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Abstractions
# ---------------------------------------------------------------------

class TextSource(Protocol):
    """
    Abstract text source.

    Implementations may load data from PDFs, files,
    databases, APIs, etc.
    """
    def exists(self) -> bool:
        ...
        
    def load(self) -> Iterable[str]: 
        ...


class VectorStore(Protocol):
    """
    Abstract vector storage interface.
    """
    def add(self, documents: List[Dict[str, str]], metadatas: List[Dict], ids: List[str]) -> None: 
        ...

    def query(self, query: str, top_k: int) -> List[Dict[str, str]]: 
        ...
    
    def clear(self) -> None: 
        ...
    
    def exists(self) -> bool: 
        ...
    
    def count(self) -> int:  
        ...

# ---------------------------------------------------------------------
# Knowledge Base
# ---------------------------------------------------------------------

class KnowledgeBase:
    """
    Knowledge base service for RAG.
    """
    def __init__(
        self, 
        source: TextSource, 
        store: VectorStore, 
        chunk_size: int = 500, 
        chunk_overlap: int = 50,
    ):
        self.source = source
        self.store = store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
            
        logger.info("KnowledgeBase initialized")
        
    # -----------------------------------------------------------------
    
    def build_index(self, force_rebuild: bool = False) -> int: 
        """
        Load source data, split it into chunks and index them.
        
        Args:
            force_rebuild: Force rebuild even if store has data
        
        Returns:
            Number of indexed chunks
        """
        
        if not force_rebuild and self.store.exists():
            doc_count = self.store.count()
            logger.info(f"Vector store already exists ({doc_count} documents), skipping build")
            return doc_count
        
        if force_rebuild:
            logger.warning("Force rebuilding index, clearing existing data...")
            self.store.clear()
        
        logger.info("Building knowledge base index")
        
        # Chunk texts        
        logger.info("Loaded %d text segments from source", len(text))
        
        if not self.source.exists():
            logger.error(f"Source does not exist: {self.source}")
            return 0
        
        # Load source texts
        text = list(self.source.load())
        
        # Chunk texts        
        logger.info("Loaded %d text segments from source", len(text))
        chunks = self._chunk_texts(text)
        
        # Handle empty cases
        if not chunks:
            logger.warning("No chunks produced")
            return 0
        
        # Add chunks to vector store
        logger.info("Created %d chunks from texts", len(chunks))
        self.store.add(
            documents=[chunk["text"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
            ids=[str(i) for i in range(len(chunks))]
        )
        
        logger.info("Indexing completed: %d chunks", len(chunks))
        return len(chunks)
    
    # -----------------------------------------------------------------

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        Perform semantic search over the knowledge base.
        """
        logger.info("Searching knowledge base for query: %s", query)
        results = self.store.query(query=query, top_k=top_k)
        logger.info("Retrieved %d results from vector store", len(results))
        return results
    
    # -----------------------------------------------------------------
    
    def clear(self) -> None:
        """
        Remove all indexed data from the knowledge base.
        """
        logger.info("Clearing knowledge base index")
        self.store.clear()
        logger.info("Knowledge base index cleared")
    
    # -----------------------------------------------------------------
    
    def _chunk_texts(self, texts: Iterable[str]) -> List[Dict[str, str]]:
        """
        Split texts into chunks with overlap.
        """
        chunks: List[Dict[str, str]] = []
        for idx, text in enumerate(texts):
            start = 0
            text_length = len(text)
            chunk_idx = 0
            while start < text_length:
                end = min(start + self.chunk_size, text_length)
                chunk_text = text[start:end]
                chunks.append({
                    "text": chunk_text, 
                    "metadata": {"source_index": idx, "chunk_index": chunk_idx, "start": start, "end": end}
                })
                if end == text_length:
                    break
                start += self.chunk_size - self.chunk_overlap
                chunk_idx += 1
        return chunks