from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from services.ai.moderation.config import ModerationResult
    
class BaseModerationModel(ABC):
    """Base class for AI moderation models."""
    
    @abstractmethod
    def moderate_text(self, text: str) -> ModerationResult:
        """
        Moderate text content.
        
        Args:
            text: Text to moderate
        
        Returns:
            ModerationResult with decision
        """
        pass
    
    @abstractmethod
    def moderate_image(self, image_data: bytes, caption: Optional[str] = None) -> ModerationResult:
        """
        Moderate image content.
        
        Args:
            image_data: Image binary data
            caption: Optional image caption
        
        Returns:
            ModerationResult with decision
        """
        pass
    
    @abstractmethod
    def moderate_voice(self, transcription: str) -> ModerationResult:
        """
        Moderate voice message.
        
        Args:
            transcription: Optional pre-transcribed text
        
        Returns:
            ModerationResult with decision
        """
        pass