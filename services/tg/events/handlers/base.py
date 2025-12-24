from abc import ABC, abstractmethod
from typing import Union

from services.tg.events import MessageEvent, UserStatusEvent, ChatActionEvent


class BaseHandler(ABC):
    """Base class for Telegram event handlers."""
    
    @abstractmethod
    def can_handle(self, event: Union[MessageEvent, UserStatusEvent, ChatActionEvent]) -> bool:
        """
        Check if this handler can process the event.
        
        Args:
            event: Normalized event object
            
        Returns:
            bool: True if handler can process this event
        """
        pass
    
    @abstractmethod
    def handle(self, event: Union[MessageEvent, UserStatusEvent, ChatActionEvent]) -> None:
        """
        Process the event.
        
        Args:
            event: Normalized event object
        """
        pass