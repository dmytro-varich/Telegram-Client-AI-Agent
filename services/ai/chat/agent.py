import logging
from typing import Optional, List, Dict

from services.ai.chat.base import BaseChatModel
from services.ai.rag.retriever import Retriever
from services.ai.chat.response import ChatResponse

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    Chat agent that orchestrates conversation logic.
    
    Combines:
    - System prompt (personality/instructions)
    - RAG retriever (knowledge base)
    - Chat model (AI API)
    - Conversation history (memory)
    """
    
    def __init__(
        self,
        chat_model: BaseChatModel,
        system_prompt: str = "You are a helpful assistant.",
        retriever: Optional[Retriever] = None,
        max_history: int = 10
    ):
        """
        Initialize chat agent.
        
        Args:
            chat_model: AI model for generating responses
            system_prompt: System instructions/personality
            retriever: RAG retriever for knowledge base (optional)
            max_history: Maximum conversation history to keep
        """
        self.chat_model = chat_model
        self.system_prompt = system_prompt
        self.retriever = retriever
        self.max_history = max_history
        
        # Conversation history per user
        self._conversations: Dict[int, List[Dict[str, str]]] = {}
        
        logger.info("ChatAgent initialized with system prompt: '%s...'", system_prompt[:50])
        if retriever:
            logger.info("RAG retriever enabled")
            
    def generate_response(
        self, 
        user_message: str, 
        user_id: int,
        clear_history: bool = False
    ) -> ChatResponse:
        """
        Generate response to user message.
        
        Args:
            user_message: User's message text
            user_id: User ID (for conversation history)
            clear_history: Whether to clear conversation history
        
        Returns:
            Generated response text
        """
        # Clear history if requested
        if clear_history:
            self._conversations[user_id] = []
        
        # Get conversation history
        history = self._conversations.get(user_id, [])
        
        # Build context from RAG if available
        rag_context = ""
        if self.retriever:
            logger.debug("Retrieving relevant documents from knowledge base")
            documents = self.retriever.retrieve(user_message, top_k=3)
            
            if documents:
                rag_context = "\n\n".join([
                    f"[Document {i+1}]\n{doc['document']}"
                    for i, doc in enumerate(documents)
                ])
                logger.debug(f"Retrieved {len(documents)} relevant documents")
        
        # Generate response
        response = self.chat_model.generate(
            system_prompt=self.system_prompt,
            user_message=user_message,
            conversation_history=history,
            rag_context=rag_context
        )
        
        # Update conversation history (only if not escalated)
        if not response.should_escalate:
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": response.message})
            
            # Keep only last N messages
            if len(history) > self.max_history * 2:
                history = history[-self.max_history * 2:]
            
            self._conversations[user_id] = history
        
        return response
            
    