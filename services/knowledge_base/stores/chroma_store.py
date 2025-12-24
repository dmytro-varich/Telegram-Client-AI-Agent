"""Wrapper for ChromaDB collection providing vector storage operations."""

import chromadb
from typing import List, Dict 

class ChromaVectorStore:
    def __init__(self, collection):
        self.collection = collection
    
    def add(self, documents: List[Dict[str, str]], metadatas: List[Dict], ids: List[str]) -> None:
        """Add documents to the collection."""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def query(self, query: str, top_k: int) -> list:
        """Perform a semantic search query on the collection."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        return [
            {
                "document": doc,
                "metadata": meta, 
                "distance": dist
            }
            for doc, meta, dist in zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
            )
        ]
        
    def clear(self) -> None:
        """Delete all documents in the collection."""
        self.collection.delete()

    def exists(self) -> bool:
        """Check if collection has documents."""
        return self.count() > 0
    
    def count(self) -> int:
        """Get number of documents in collection."""
        return self.collection.count()