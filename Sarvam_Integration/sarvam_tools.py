import os
import logging
from typing import Optional
from sarvamai import SarvamAI

logger = logging.getLogger(__name__)

def get_sarvam_client() -> Optional[SarvamAI]:
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        logger.warning("SARVAM_API_KEY environment variable is not set. Sarvam AI endpoints will fail.")
        return None
    return SarvamAI(api_subscription_key=api_key)

def tool_translate_text(text: str, target_language_code: str = "hi-IN", source_language_code: str = "en-IN") -> str:
    """
    Translates text to a target Indic language or English using Sarvam AI.
    Provide the 'text' to translate.
    Optionally provide 'target_language_code' (default is 'hi-IN' Hindi).
    Other common target language codes: 'bn-IN' (Bengali), 'ta-IN' (Tamil), 'te-IN' (Telugu), 'mr-IN' (Marathi), 'en-IN' (English).
    """
    client = get_sarvam_client()
    if not client:
        return "Error: Sarvam API key not configured in environment variables (.env). Cannot translate text."
    
    try:
        response = client.text.translate(
            input=text,
            source_language_code=source_language_code,
            target_language_code=target_language_code,
            speaker_gender="Male"  # required by some Sarvam text/voice endpoints
        )
        return str(response)
    except Exception as e:
        logger.error(f"Sarvam translation error: {e}")
        return f"Translation failed: {str(e)}"
