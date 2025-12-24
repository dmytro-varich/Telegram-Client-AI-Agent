from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from services.ai.chat.response import ChatResponse

class BaseChatModel(ABC):
    """Base class for chat AI models."""
    
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        rag_context: Optional[str] = None
    ) -> ChatResponse:
        """
        Generate chat response.
        
        Args:
            system_prompt: System instructions/personality
            user_message: User's current message
            conversation_history: Previous conversation messages
            rag_context: Retrieved knowledge base documents
        
        Returns:
            ChatResponse with structured data
        """
        pass