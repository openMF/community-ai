import os
import logging
import base64
from typing import Optional
from sarvamai import SarvamAI

logger = logging.getLogger(__name__)

# Map the frontend provided 2-letter codes to what Sarvam TTS generally expects conceptually
# For TTS, language code specifics depend highly on Bulbul API strictness. Usually standard codes work.
TTS_LANGUAGE_MAP = {
    "en": "en-IN", # English (India)
    "hi": "hi-IN", # Hindi
    "ta": "ta-IN", # Tamil
    "te": "te-IN", # Telugu
    "bn": "bn-IN", # Bengali
    "mr": "mr-IN", # Marathi
    "gu": "gu-IN", # Gujarati
    "kn": "kn-IN", # Kannada
    "ml": "ml-IN", # Malayalam
    "pa": "pa-IN", # Punjabi
    "or": "od-IN"  # Odia (Sarvam SDK uses od-IN)
}

def get_sarvam_client() -> Optional[SarvamAI]:
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        logger.error("SARVAM_API_KEY is missing! Set it in your .env.")
        return None
    return SarvamAI(api_subscription_key=api_key)

async def generate_speech(text: str, language: str, output_file: str) -> Optional[str]:
    """
    Generate speech from text using Sarvam's TTS endpoints.
    Saves the generated audio to `output_file` (usually WAV).
    """
    client = get_sarvam_client()
    if not client:
        return None
        
    sarvam_lang_code = TTS_LANGUAGE_MAP.get(language, "en-IN")

    try:
        # Assuming Sarvam provides a text_to_speech client method. 
        # Using the standard SDK pattern based on documentation.
        response = client.text_to_speech.convert(
            text=text,
            target_language_code=sarvam_lang_code,
            speaker="tanya", # From valid enum of Bulbul v3 speakers
            pace=1.0,
            model="bulbul:v3"
        )
        
        # Typically the audio is returned as Base64 in the response
        if response and hasattr(response, 'audios') and len(response.audios) > 0:
            audio_base64 = response.audios[0]
            with open(output_file, "wb") as f:
                f.write(base64.b64decode(audio_base64))
            return output_file
        else:
            logger.error("Sarvam TTS did not return audio data.")
            return None
            
    except Exception as e:
        logger.error(f"Error calling Sarvam TTS: {e}")
        return None
