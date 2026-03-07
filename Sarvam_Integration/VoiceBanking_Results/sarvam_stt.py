import os
import re
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
                mode=mode  # 'transcribe' outputs native script, 'translate' outputs English
            )

            # Try to extract transcript robustly from different response shapes.
            # 1) If response has attribute-like access
            transcript = None
            try:
                if hasattr(response, "transcript"):
                    transcript = getattr(response, "transcript")
                elif hasattr(response, "text"):
                    transcript = getattr(response, "text")
            except Exception:
                transcript = None

            # 2) If response is a dict-like
            if transcript is None:
                try:
                    if isinstance(response, dict):
                        for key in ("transcript", "text", "transcription", "result"):
                            if key in response and response[key]:
                                transcript = response[key]
                                break
                except Exception:
                    transcript = None

            # 3) Fallback: parse string representation for patterns like transcript='...'
            if transcript is None:
                resp_str = str(response)
                # pattern: transcript='...'
                m = re.search(r"transcript=['\"]([^'\"]+)['\"]", resp_str)
                if m:
                    transcript = m.group(1)
                else:
                    # try simple quoted content after "transcript=" until comma
                    m2 = re.search(r"transcript=([^,\s]+)", resp_str)
                    if m2:
                        transcript = m2.group(1)

            # Final fallback: use entire string
            if transcript is None:
                transcript = str(response)

            logger.info(f"Sarvam STT Transcript: {transcript}")
            return transcript
    except Exception as e:
        logger.error(f"Error calling Sarvam STT: {e}")
        return None
