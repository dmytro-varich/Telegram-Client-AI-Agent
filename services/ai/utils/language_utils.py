import logging
import detectlanguage
from deep_translator import GoogleTranslator

from config import DETECT_LANG_KEY

detectlanguage.configuration.api_key = DETECT_LANG_KEY

logger = logging.getLogger(__name__)

def translate_text(text: str = 'auto', target_language: str = 'en') -> str:
    """
    Translate text to the target language using Google Translate.
    
    Args:
        text: Text to translate
        target_language: Target language code (e.g., 'en', 'fr', 'de')
        
    Returns:
        Translated text or text if error
    """
    try: 
        translator = GoogleTranslator(target=target_language)
        translated_text = translator.translate(text)
        return translated_text
    except Exception as e: 
        logger.error(f"Error translating text: {e}")
        return text


def detect_language(text: str) -> str:
    """
    Detect the language of the given text using Google Translate.
    
    Args:
        text: Text to detect language for
        
    Returns:
        Detected language code (e.g., 'en', 'fr', 'de') or return 'en' on error
    """
    try: 
        return detectlanguage.detect_code(text)
    except Exception as e: 
        logger.error(f"Error detecting language: {e}")
        return 'en'