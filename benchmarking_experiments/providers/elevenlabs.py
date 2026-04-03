# benchmarking_experiments/providers/elevenlabs.py

import os
import io
import time
from typing import AsyncGenerator, Dict, Any
from dotenv import load_dotenv
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings
import httpx
from .base import TTSProvider, STTProvider

load_dotenv()

VOICE_IDS = {
    "en": "JBFqnCBsd6RMkjVDRZzb",  # George - English
    "hi": "JBFqnCBsd6RMkjVDRZzb",  # George - supports Hindi
    "es": "JBFqnCBsd6RMkjVDRZzb",  # George - supports Spanish
}

LANGUAGE_CODES = {
    "en": "en",
    "hi": "hi",
    "es": "es",
}


class ElevenLabsTTSProvider(TTSProvider):
    """
    ElevenLabs TTS Provider implementing TTSProvider base class.
    Supports English (en), Hindi (hi), and Spanish (es).
    Uses ElevenLabs Flash v2.5 model for low latency.
    """

    def __init__(self, language: str = "en"):
        self.language = language
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not set in environment")
        self.voice_id = VOICE_IDS.get(language, VOICE_IDS["en"])
        self.client = AsyncElevenLabs(api_key=self.api_key)

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Yields synthesized audio chunks from ElevenLabs TTS.
        Uses Flash v2.5 for low latency multilingual output.
        """
        async for chunk in self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id="eleven_flash_v2_5",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
            ),
            output_format="mp3_44100_128",
        ):
            if chunk:
                yield chunk


class ElevenLabsSTTProvider(STTProvider):
    """
    ElevenLabs STT Provider implementing STTProvider base class.
    Uses ElevenLabs Scribe model — supports 90+ languages including Hindi.
    """

    def __init__(self, language: str = "en"):
        self.language = language
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not set in environment")
        self.client = AsyncElevenLabs(api_key=self.api_key)

    async def transcribe_stream(
        self, audio_generator: AsyncGenerator[bytes, None]
    ) -> Dict[str, Any]:
        """
        Collects audio chunks and transcribes via ElevenLabs Scribe STT.
        """
        audio_data = b""
        async for chunk in audio_generator:
            audio_data += chunk

        start = time.time()

        result = await self.client.speech_to_text.convert(
            file=("audio.mp3", io.BytesIO(audio_data), "audio/mpeg"),
            model_id="scribe_v1",
            language_code=LANGUAGE_CODES.get(self.language, "en"),
        )

        latency_ms = round((time.time() - start) * 1000, 2)

        return {
            "text": result.text,
            "language": self.language,
            "latency_ms": latency_ms,
            "model": "scribe_v1",
        }