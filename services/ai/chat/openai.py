import logging
import json
from typing import List, Dict, Optional
from pydantic import BaseModel

from openai import OpenAI

from services.ai.chat.base import BaseChatModel
from services.ai.chat.response import ChatResponse

from services.ai.utils import translate_text, detect_language

logger = logging.getLogger(__name__)


class ResponseSchema(BaseModel):
    """Pydantic schema for structured output."""
    message: str
    should_escalate: bool = False
    escalation_reason: Optional[str] = None
    confidence: float = 1.0
    language: Optional[str] = None
    

class OpenAIGPTModel(BaseChatModel):
    """Adapter for OpenAI Chat Model"""
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized OpenAI model: {model}")
        
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        rag_context: Optional[str] = None
    ) -> BaseChatModel:
        """
        Generate response using OpenAI API.
        
        Args:
            system_prompt: System instructions
            user_message: Current user message
            conversation_history: Previous messages
            rag_context: Retrieved documents from RAG
        
        Returns:
            ChatResponse with structured data
        """
        messages = []
        
        # Add system prompt
        system_content = system_prompt
        if rag_context:
            system_content += f"\n\nRelevant information:\n{rag_context}"
            
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
            
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Detect user language
        user_language = detect_language(user_message)
        
        try:
            logger.debug(f"Sending structured request to OpenAI: {len(messages)} messages")
            
            response = self.client.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=ResponseSchema,
                temperature=0.3,
                max_tokens=300
            )
            
            # Parse structured response
            parsed = response.choices[0].message.parsed
            
            chat_response = ChatResponse(
                message=parsed.message,
                should_escalate=parsed.should_escalate,
                escalation_reason=parsed.escalation_reason,
                confidence=parsed.confidence,
                language=parsed.language or user_language
            )
            
            logger.debug(f"Structured response: {chat_response}")            
            return chat_response
        except Exception as e:
            logger.error(f"OpenAI chat API error: {e}")
            default_reply = "I'm sorry, I couldn't process your request at the moment."
            translated_message = translate_text(default_reply, target_language=user_language)
            return ChatResponse(
                message=translated_message,
                should_escalate=True,
                escalation_reason="API error",
                confidence=0.0, 
                language=user_language
            )