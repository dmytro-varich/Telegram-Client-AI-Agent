import logging
import base64
from openai import OpenAI
from services.ai.moderation.base import BaseModerationModel
from services.ai.moderation.config import ModerationResult

from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class OpenAIModerationModel(BaseModerationModel): 
    """Adapter for OpenAI Moderation Model"""
    def __init__(self, api_key: str, model: str = "omni-moderation-latest"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def moderate_text(self, text: str, context: Optional[Dict[str, Any]] = None) -> ModerationResult:
        """Moderate text using OpenAI moderation API."""
        try:
            # Use OpenAI Moderation API
            response = self.client.moderations.create(input=text, model=self.model)
            result = response.results[0]

            # Check for violations
            if result.flagged:
                categories = [cat for cat, flagged in result.categories.model_dump().items() if flagged]
                
                return ModerationResult(
                    should_delete=True,
                    reason=', '.join(categories),
                    confidence=max(result.category_scores.model_dump().values()),
                    violations=categories
                )
            
            return ModerationResult(
                should_delete=False,
                reason="Content is acceptable",
                confidence=0.95
            )
        except Exception as e:
            logger.error("OpenAI moderation API error: %s", e)
            return ModerationResult(should_delete=False, reason="API error")
        
    def moderate_image(self, image_data: bytes, caption: Optional[str] = None) -> ModerationResult:
        """Moderate image using OpenAI (stub implementation)."""
        try:
            input_data = []
            
            # Convert bytes to base64 (это делается здесь, на уровне Model!)
            image_b64 = base64.b64encode(image_data).decode('utf-8')
        
            if caption:
                input_data.append({"type": "text", "text": caption})
                
            if image_b64:
                input_data.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                })
                
            if not input_data:
                raise ValueError("No input data for moderation")
            
            response = self.client.moderations.create(
                model=self.model,
                input=input_data
            )
            result = response.results[0]
            
            if result.flagged:
                categories = [cat for cat, flagged in result.categories.model_dump().items() if flagged]
                return ModerationResult(
                    should_delete=True,
                    reason=', '.join(categories),
                    confidence=max(result.category_scores.model_dump().values()),
                    violations=categories
                )
                
            return ModerationResult(
                should_delete=False,
                reason="Content is acceptable",
                confidence=0.95
            )
        except Exception as e:
            logger.error("OpenAI moderation API error: %s", e)
            return ModerationResult(should_delete=False, reason="API error")
        
    def moderate_voice(self, transcription: str) -> ModerationResult:
        """Moderate voice transcription using OpenAI moderation API."""
        return self.moderate_text(transcription)