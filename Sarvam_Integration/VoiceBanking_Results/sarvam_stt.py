import os
import logging
from typing import Optional
from sarvamai import SarvamAI

logger = logging.getLogger(__name__)

# Sarvam supports these languages natively via Saaras v3:
# hi, ta, te, ml, pa, bn, gu, mr, kn, or, ur, as, as-bn, hi-latn, en
# All of these are standard 2-letter codes.

def get_sarvam_client() -> Optional[SarvamAI]:
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        logger.error("SARVAM_API_KEY is missing! Set it in your .env.")
        return None
    return SarvamAI(api_subscription_key=api_key)

def transcribe_audio_file(file_path: str, language: str = "en", mode: str = "transcribe") -> Optional[str]:
    """
    Transcribes an audio file into text using Sarvam's Saaras STT model.
    'language' can be passed but Saaras is auto-detecting for the languages it supports.
    """
    client = get_sarvam_client()
    if not client:
        return None
        
    try:
        with open(file_path, "rb") as f:
            response = client.speech_to_text.transcribe(
                file=f,
                model="saaras:v3",
                mode=mode # 'transcribe' outputs native script, 'translate' outputs English
            )
            # Response object format usually provides text directly or via a property
            # For logging and safety, convert to string and return
            result = str(response) 
            logger.info(f"Sarvam STT Result: {result}")
            return result
    except Exception as e:
        logger.error(f"Error calling Sarvam STT: {e}")
        return None
