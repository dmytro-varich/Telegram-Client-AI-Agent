from services.knowledge_base import KnowledgeBase

class Retriever:
    """Retriever for RAG using a Knowledge Base."""
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        
    def retrieve(self, query: str, top_k: int = 3) -> list:
        """
        Retrieve relevant documents from the knowledge base.
        """
        return self.kb.store.query(query=query, top_k=top_k)