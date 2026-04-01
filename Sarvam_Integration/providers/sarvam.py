import os
import logging
import base64
import re
from typing import Optional
from sarvamai import SarvamAI
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class SarvamProvider:
    LANG_MAP = {
        "en": "en-IN", "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN",
        "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN",
        "pa": "pa-IN"
    }

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("SARVAM_API_KEY")
        self.client = SarvamAI(api_subscription_key=key) if key else None
        if not self.client:
            logger.error("SARVAM_API_KEY missing - client disabled")

    def speech_to_text(self, file_path: str, mode: str = "transcribe", lang_code: str = None) -> Optional[str]:
        if not self.client: return None
        try:
            with open(file_path, "rb") as f:
                res = self.client.speech_to_text.transcribe(file=f, model="saaras:v3", mode=mode)
            
            # Unified parsing for diverse response formats
            if hasattr(res, 'transcript'): return res.transcript
            if isinstance(res, dict) and 'transcript' in res: return res['transcript']
            
            # Fallback to string regex for complex objects
            match = re.search(r"transcript=['\"]([^'\"]+)['\"]", str(res))
            return match.group(1) if match else str(res)
        except Exception as e:
            logger.error(f"STT: {e}")
            return None

    def text_to_speech(self, text: str, lang: str, output_path: str) -> Optional[str]:
        if not self.client: return None
        try:
            res = self.client.text_to_speech.convert(
                text=text,
                target_language_code=self.LANG_MAP.get(lang, "en-IN"),
                speaker="tanya",
                model="bulbul:v3"
            )
            if res and hasattr(res, 'audios') and res.audios:
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(res.audios[0]))
                return output_path
        except Exception as e:
            logger.error(f"TTS: {e}")
        return None
    def translate(self, text: str, source_lang: str = "en-IN", target_lang: str = "hi-IN") -> Optional[str]:
        if not self.client: return None
        try:
            res = self.client.text.translate(
                input=text,
                source_language_code=source_lang,
                target_language_code=target_lang
            )
            # Response handling for translation
            if hasattr(res, 'translated_text'): return res.translated_text
            if isinstance(res, dict) and 'translated_text' in res: return res['translated_text']
            return str(res)
        except Exception as e:
            logger.error(f"Translate: {e}")
            return None
