from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, List, Dict

from services.tg.events.enums import ChatType

@dataclass
class SenderInfo:
    """Information about the sender of a message."""
    user_id: int
    username: str = ''
    first_name: str = ''
    last_name: str = ''
    phone: str = ''

    @property
    def full_name(self) -> str:
        """Get the full name of the sender."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def mention(self) -> str:
        """Get a mention string for the sender."""
        if self.username:
            return f"@{self.username}"
        return self.full_name or str(self.user_id)

@dataclass
class MediaInfo:
    """Information about media content in a message."""
    media_type: str  # 'photo', 'video', 'voice', 'document', etc.
    file_id: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    duration: Optional[int] = None  # For video/voice/audio
    width: Optional[int] = None  # For photo/video
    height: Optional[int] = None  # For photo/video
    thumbnail: Optional[Dict[str, Any]] = None
    caption: Optional[str] = None  # Caption text for media

@dataclass
class MessageEvent:
    """Normalized message event from any Telegram client."""
    
    # --- Core Identifiers ---
    message_id: int          # Message ID 
    chat_id: int             # Unified chat ID 
    sender_id: int           # ID of the sender 
    
    # --- Sender Information ---
    sender: SenderInfo
    
    # --- Content ---
    text: str                # Plain message text
    raw_text: str            # Text with markup (Markdown/HTML)
    
    # --- Timestamps ---
    date: datetime           # Send time (as datetime object)
    edit_date: Optional[datetime] = None
    
    # --- Chat Type ---
    chat_type: ChatType = ChatType.UNKNOWN
    
    # --- State Flags ---
    is_outgoing: bool = False # Sent by us or received?
    is_mention: bool = False  # Are we mentioned in this message?
    is_service: bool = False  # Service message (added to group, etc.)
    
    # --- Media ---
    has_media: bool = False
    media: Optional[MediaInfo] = None  # Media information
    
    # --- Replies and Forwards ---
    reply_to_message_id: Optional[int] = None
    forward_from_chat_id: Optional[int] = None
    
    # --- Client Reference ---
    client: Any = field(default=None, repr=False)  # Reference to Telegram client instance
    
    # --- Internal Data ---
    raw_event: Any = field(default=None, repr=False)  # Reference to original object (dict or Message)
    

@dataclass
class UserStatusEvent:
    """User online/offline status change."""
    user_id: int
    is_online: bool
    last_seen: Optional[datetime] = None
    client: Any = field(default=None, repr=False)
    raw_event: Any = field(default=None, repr=False)


@dataclass
class ChatActionEvent:
    """User is typing, recording voice, etc."""
    chat_id: int
    user_id: int
    action: str  # 'typing', 'recording_video', 'uploading_photo', etc.
    client: Any = field(default=None, repr=False)
    raw_event: Any = field(default=None, repr=False)