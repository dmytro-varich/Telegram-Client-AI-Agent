import logging
from datetime import datetime
from typing import List, Dict, Any, Union, Optional

from services.tg.events.handlers import BaseHandler
from services.tg.events import MessageEvent, UserStatusEvent, ChatActionEvent, MediaInfo, SenderInfo
from services.tg.events.enums import ChatType

logger = logging.getLogger(__name__)


class EventRouter:
    """
    Routes normilized Telegram events to appropriate handlers.
    """
    
    def __init__(self):
        self.handlers: List[BaseHandler] = []
        
    def add_handler(self, handler: BaseHandler) -> None:
        """Register a new event handler."""
        self.handlers.append(handler)
        logger.info("Registered handler: %s", handler.__class__.__name__)

    def route(self, update: Dict[str, Any], client) -> None:
        """
        Convert raw update to normalized event and route to handlers.
        
        Args:
            update: Raw update from Telegram client
            client: The client instance that received the update
        """
        # Convert raw update to normalized event
        event = self._normalize_event(update, client)
        
        if not event:
            logger.warning("Could not normalize update: %s", update)
            return
        
        # Pass event to all handlers that can handle it
        for handler in self.handlers:
            try:
                if handler.can_handle(event):
                    handler.handle(event)
            except Exception as e:
                logger.exception(
                    "Error in handler %s: %s", 
                    handler.__class__.__name__, 
                    str(e)
                )   
                
        logger.debug(f"No handler found for event: {event.__class__.__name__}")
     
    def _normalize_event(
        self, 
        update: Dict[str, Any], 
        client
    ) -> Union[MessageEvent, UserStatusEvent, ChatActionEvent, None]:
        """
        Normalize raw update to a standard event object.
        
        Args:
            update: Raw update from Telegram client
            client: The client instance that received the update
            
        Returns:
            Normalized event object or None if unsupproted
        """
        # Detect update type (TDLib format)
        if '@type' in update:
            return self._from_tdlib(update, client)

        # TODO: Add Telethon/Pyrogram support
        # if isinstance(update, telethon.events.NewMessage):
        #     return self._from_telethon(update, client)

        return None
    
    def _from_tdlib(
        self,
        update: Dict[str, Any],
        client
    ) -> Union[MessageEvent, UserStatusEvent, ChatActionEvent, None]:
        """Convert TDLib update to normalized event."""
        update_type = update.get('@type')

        # New message
        if update_type == 'updateNewMessage':
            logger.debug('Processing TDLib new message update')
            return self._tdlib_to_message_event(update['message'], client, update)
            
        # Message edited
        elif update_type == 'updateMessageEdited':
            message = client.client.call_method('getMessage', (
                'chat_id', update['chat_id'],
                'message_id', update['message_id']
            ))
            message.wait()
            if not message.error:
                return self._tdlib_to_message_event(message.update, client, update)            
            
        # User status
        elif update_type == 'updateUserStatus':
            return UserStatusEvent(
                user_id=update['user_id'],
                is_online=update.get('status', {}).get('@type') == 'userStatusOnline',
                client=client,
                raw_event=update
            )
        
        # Chat action (typing, etc.)
        if update_type == 'updateChatAction':
            return ChatActionEvent(
                chat_id=update['chat_id'],
                user_id=update.get('sender_id', {}).get('user_id', 0),
                action=update.get('action', {}).get('@type', 'unknown'),
                client=client,
                raw_event=update
            )

        return None
        
    def _tdlib_to_message_event(
        self,
        message: Dict[str, Any],
        client,
        raw_update: Dict[str, Any]
    ) -> MessageEvent:
        """Convert TDLib message dict to MessageEvent."""
        
        logger.debug(f"Converting TDLib message to MessageEvent: message_id={message['id']}, chat_id={message['chat_id']}")
        
        content = message.get('content', {})
        content_type = content.get('@type', '')
    
        # Extract text content (message text or media caption)
        text = '' 
        caption = ''
        
        if content_type == 'messageText':
            text = content.get('text', {}).get('text', '')
        else:
            # For media messages, try to get caption
            caption_obj = content.get('caption', {})
            if isinstance(caption_obj, dict):
                caption = caption_obj.get('text', '')
            text = caption  # Use caption as text for media messages
         
        # Determine chat type based on chat_id    
        chat_id = message['chat_id']
        if chat_id > 0:
            # Positive ID = private chat
            chat_type = ChatType.PRIVATE
        elif str(chat_id).startswith('-100'):
            # -100xxxxxxxxx = supergroup/channel
            chat_type = ChatType.SUPERGROUP
        elif chat_id < 0:
            # Negative ID (not -100...) = basic group
            chat_type = ChatType.GROUP
        else:
            chat_type = ChatType.UNKNOWN    
        
        # Extract sender ID
        sender_id = message.get('sender_id', {}).get('user_id', 0)
        
        # Get sender info (name, username)
        sender_info = self._get_sender_info(sender_id, client)
        
        # Extract media information
        media_info = None
        has_media = content_type != 'messageText'
    
        # Check if message has media
        content_type = message.get('content', {}).get('@type', '')
        is_text_only = content_type == 'messageText'

        if has_media:
            media_info = self._extract_media_info(content, content_type)
            logger.debug(f"Message {message['id']} has media: {media_info.media_type if media_info else 'unknown'}")

        return MessageEvent(
            message_id=message['id'],
            chat_id=chat_id,
            sender_id=sender_id,
            sender=sender_info,
            text=text,
            raw_text=text,
            date=datetime.fromtimestamp(message['date']),
            edit_date=datetime.fromtimestamp(message['edit_date']) if message.get('edit_date', 0) > 0 else None,
            chat_type=chat_type,
            is_outgoing=message.get('is_outgoing', False),
            is_mention=message.get('contains_unread_mention', False),
            is_service=content_type.startswith('messageService') if content_type else False,
            has_media=has_media,
            media=media_info,
            reply_to_message_id=message.get('reply_to_message_id'),
            forward_from_chat_id=message.get('forward_info', {}).get('from_chat_id'),
            client=client,
            raw_event=raw_update
        )
        
    def _extract_media_info(self, content: Dict[str, Any], content_type: str) -> Optional[MediaInfo]:
        """
        Extract media information from TDLib message content.
        
        Args:
            content: Message content object from TDLib
            content_type: Type of content (e.g., 'messagePhoto', 'messageVideo')
        
        Returns:
            MediaInfo object or None if no media
        """
        from services.tg.events.event import MediaInfo

        # Remove 'message' prefix: 'messagePhoto' -> 'photo'
        media_type = content_type.replace('message', '').lower() if content_type.startswith('message') else 'unknown'

        # Extract caption
        caption_obj = content.get('caption', {})
        caption = caption_obj.get('text', '') if isinstance(caption_obj, dict) else ''
        
        media_info = MediaInfo(
            media_type=media_type,
            caption=caption
        )
        
        # Extract type-specific fields
        if content_type == 'messagePhoto':
            photo = content.get('photo', {})
            sizes = photo.get('sizes', [])
            if sizes:
                largest = max(sizes, key=lambda s: s.get('width', 0) * s.get('height', 0))
                media_info.width = largest.get('width')
                media_info.height = largest.get('height')
                media_info.file_id = largest.get('photo', {}).get('id')
                media_info.file_size = largest.get('photo', {}).get('size')

        elif content_type == 'messageVideo':
            video = content.get('video', {})
            media_info.duration = video.get('duration')
            media_info.width = video.get('width')
            media_info.height = video.get('height')
            media_info.file_id = video.get('video', {}).get('id')
            media_info.file_size = video.get('video', {}).get('size')
            media_info.mime_type = video.get('mime_type')
        
        elif content_type == 'messageVoiceNote':
            voice = content.get('voice_note', {})
            media_info.duration = voice.get('duration')
            media_info.file_id = voice.get('voice', {}).get('id')
            media_info.file_size = voice.get('voice', {}).get('size')
            media_info.mime_type = voice.get('mime_type', 'audio/ogg')
        
        elif content_type == 'messageAudio':
            audio = content.get('audio', {})
            media_info.duration = audio.get('duration')
            media_info.file_id = audio.get('audio', {}).get('id')
            media_info.file_size = audio.get('audio', {}).get('size')
            media_info.mime_type = audio.get('mime_type')
        
        elif content_type == 'messageDocument':
            document = content.get('document', {})
            media_info.file_id = document.get('document', {}).get('id')
            media_info.file_size = document.get('document', {}).get('size')
            media_info.mime_type = document.get('mime_type')
        
        elif content_type == 'messageSticker':
            sticker = content.get('sticker', {})
            media_info.width = sticker.get('width')
            media_info.height = sticker.get('height')
            media_info.file_id = sticker.get('sticker', {}).get('id')
        
        elif content_type == 'messageAnimation':
            animation = content.get('animation', {})
            media_info.duration = animation.get('duration')
            media_info.width = animation.get('width')
            media_info.height = animation.get('height')
            media_info.file_id = animation.get('animation', {}).get('id')
            media_info.file_size = animation.get('animation', {}).get('size')
            media_info.mime_type = animation.get('mime_type')
            
        return media_info
    
    def _get_sender_info(self, sender_id: int, client) -> SenderInfo:
        """
        Retrieve sender information given a sender ID.
        
        Args:
            sender_id: ID of the message sender
            client: The client instance to fetch user info
            
        Returns:
            SenderInfo object with user details
        """
        user_info = client.get_user(sender_id)
        logger.debug(f"Fetched sender info for user_id={sender_id}: {user_info}")
        
        if not user_info:
            logger.warning(f"Could not fetch user info for user_id={sender_id}")
            return SenderInfo(user_id=sender_id, first_name=f"User{sender_id}")
        
        username = None
        
        usernames_obj = user_info.get('usernames', {})
        if isinstance(usernames_obj, dict):
            username = usernames_obj.get('editable_username', '')
        
        if user_info:
            return SenderInfo(
                user_id=sender_id,
                username=username,
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', ''),
                phone=user_info.get('phone_number', ''),
            )
        else:
            return SenderInfo(user_id=sender_id)