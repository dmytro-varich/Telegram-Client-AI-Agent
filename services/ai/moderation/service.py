import logging
from typing import Dict

import os
import tempfile


from services.ai.moderation.base import BaseModerationModel
from services.tg.events import MessageEvent
from services.ai.moderation.config import ModerationResult

logger = logging.getLogger(__name__)    

class ModerationService:
    """
    Service for moderating Telegram messages.
    
    Orchestrates different moderation models and handles different content types.
    """
    def __init__(self, model: BaseModerationModel):
        """
        Initialize moderation service.
        
        Args:
            model: AI moderation model to use
        """
        self.model = model
        self._whisper_model = None
        logger.info("ModerationService initialized with %s", model.__class__.__name__)

    def moderate_message(self, event: MessageEvent) -> ModerationResult:
        """
        Moderate a message event (text, media, voice, etc.).
        
        Args:
            event: Normalized message event
        
        Returns:
            ModerationResult with decision
        """
        # Text-only message
        if not event.has_media and event.text:
            logger.info("Moderating text message: %s", event.message_id)
            return self.model.moderate_text(event.text)
        
        # Media with caption
        if event.has_media and event.media:
            logger.debug("Moderating %s message: %s", event.media.media_type, event.message_id)
            
            # Photo
            if event.media.media_type == 'photo':
                return self._moderate_photo(event)
            
            # Voice note
            elif event.media.media_type in ('voicenote', 'voice'):
                return self._moderate_voice(event)
            
            # Video
            elif event.media.media_type == 'video':
                return ModerationResult(should_delete=False, reason="No content to moderate")
            
            # Other media types (documents, stickers, etc.)
            else:
                # Just moderate caption if present
                if event.media.caption:
                    return self.model.moderate_text(event.media.caption)
                
        # No content to moderate
        logger.debug("No content to moderate in message %s", event.message_id)
        return ModerationResult(should_delete=False, reason="No content to moderate")

    def _moderate_photo(self, event: MessageEvent) -> Dict:
        """Moderate photo message."""
        try: 
            # Download photo from Telegram
            image_data = self._download_file(event.client, event.media.file_id)
            
            if not image_data:
                logger.warning("Failed to download photo %s", event.message_id)
                # Fallback to caption moderation only
                if event.media.caption:
                    return self.model.moderate_text(event.media.caption, context)
                return ModerationResult(should_delete=False, reason="Failed to download media")
            
            # Moderate image with AI
            return self.model.moderate_image(image_data, event.media.caption)
        except Exception as e:
            logger.exception("Error moderating photo: %s", str(e))
            return ModerationResult(should_delete=False, reason="Moderation error")
        
    def _moderate_voice(self, event: MessageEvent) -> Dict:
        """Moderate voice message."""
        try:
            # Download voice from Telegram
            audio_data = self._download_file(event.client, event.media.file_id)
            
            if not audio_data:
                logger.warning("Failed to download voice %s", event.message_id)
                # Fallback to caption moderation only
                if event.media.caption:
                    return self.model.moderate_text(event.media.caption)
                return ModerationResult(should_delete=False, reason="Failed to download media")
            
            # Transcribe voice to text
            transcription = self._transcribe_voice(audio_data)
            
            if not transcription:
                logger.warning("Failed to transcribe voice %s", event.message_id)
                return ModerationResult(should_delete=False, reason="Failed to transcribe voice")
            
            # Moderate voice with AI
            return self.model.moderate_voice(transcription)
        except Exception as e:
            logger.exception("Error moderating voice: %s", str(e))
            return ModerationResult(should_delete=False, reason="Moderation error")
    
    def _download_file(self, client, file_id: str) -> bytes | None:
        """
        Download file from Telegram client.
        
        Args:
            client: TDLib client instance
            file_id: File ID to download
            
        Returns:
            File binary data or None
        """
        try: 
            # Get file info
            file_result = client.client.call_method('getFile', params={'file_id': file_id})
            file_result.wait()
            
            if file_result.error:
                logging.error(f"Failed to get file info: {file_result.error}")
                return None
            
            file_info = file_result.update
            local_path = file_info.get('local', {}).get('path', '')
            is_downloaded = file_info.get('local', {}).get('is_downloading_completed', False)
            
            # Download if not already downloaded
            if not local_path or not is_downloaded:
                logger.debug(f"Downloading file {file_id}...")
                download_result = client.client.call_method(
                    'downloadFile',
                    params={
                        'file_id': file_id,
                        'priority': 32,
                        'synchronous': True
                    }
                )
                download_result.wait()
                
                if download_result.error:
                    logger.error(f"Error downloading file: {download_result.error}")
                    return None
                
                local_path = download_result.update.get('local', {}).get('path', '')
            
            # Read file as bytes
            if local_path and os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    file_bytes = f.read()
                
                logger.info(f"Downloaded file {file_id}: {len(file_bytes)} bytes")
                return file_bytes
            
            logger.error(f"File path not found for {file_id}")
            return None
        except Exception as e:
            logging.error(f"Exception occurred while downloading file: {e}")
            return None
        
    def _transcribe_voice(self, audio_data: bytes) -> str | None:
        """
        Transcribe voice audio to text using Whisper.
        
        Args:
            audio_data: Audio file binary data
            
        Returns:
            Transcribed text or None
        """ 
        try: 
            # Lazy load Whisper model
            if not self._whisper_model:
                import whisper
                logger.info("Loading Whisper model (base)...")
                self._whisper_model = whisper.load_model("base")  # tiny/base/small/medium/large
                logger.info("Whisper model loaded successfully")
            
            # Save audio data to temporary file (Whisper needs file path)
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
                
            try:
                # Transcribe audio
                logger.debug(f"Transcribing audio file: {temp_path}")
                result = self._whisper_model.transcribe(
                    temp_path,
                    language=None,  # Auto-detect language
                    fp16=False      # Disable FP16 for CPU compatibility
                )
                
                transcribed_text = result['text'].strip()
                detected_language = result.get('language', 'unknown')
                
                logger.info(
                    f"Voice transcribed: '{transcribed_text[:50]}...' (lang: {detected_language})"
                )
                
                return transcribed_text
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except ImportError: 
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            return None
        except Exception as e:
            logger.exception(f"Failed to transcribe voice: {e}")
            return None