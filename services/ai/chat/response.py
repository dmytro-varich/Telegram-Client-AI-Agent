from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class ChatResponse:
    """Structured response from chat model."""
    
    message: str  
    should_escalate: bool = False
    escalation_reason: Optional[str] = None
    confidence: float = 1.0
    language: Optional[str] = None
    
    def to_telegram_message(self) -> str:
        """Convert to message for sending to Telegram."""
        return self.message