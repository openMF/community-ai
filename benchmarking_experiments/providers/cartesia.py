# benchmarking_experiments/providers/cartesia.py

import os
import io
import wave
from typing import AsyncGenerator, Dict, Any
from dotenv import load_dotenv
from cartesia import AsyncCartesia, Cartesia

from .base import TTSProvider, STTProvider

load_dotenv()

VOICE_IDS = {
    "en": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
    "hi": "bdab08ad-4137-4548-b9db-6142854c7525",
    "es": "59b37da2-92ba-401a-9e4e-b1d16898d9bc",
}

SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH = 4  # pcm_f32le = 4 bytes per sample


def pcm_to_wav(pcm_data: bytes) -> bytes:
    """Wrap raw PCM bytes in a proper WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)
    return buf.getvalue()


class CartesiaTTSProvider(TTSProvider):
    """
    Cartesia TTS Provider implementing TTSProvider base class.
    Supports English (en), Hindi (hi), and Spanish (es).
    Uses Cartesia sonic-2 model with async streaming.
    """

    def __init__(self, language: str = "en"):
        self.language = language
        self.voice_id = VOICE_IDS.get(language, VOICE_IDS["en"])
        self.api_key = os.getenv("CARTESIA_API_KEY")
        if not self.api_key:
            raise ValueError("CARTESIA_API_KEY not set in environment")

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        async with AsyncCartesia(api_key=self.api_key) as client:
            async for chunk in await client.tts.bytes(
                model_id="sonic-2",
                transcript=text,
                voice={"mode": "id", "id": self.voice_id},
                language=self.language,
                output_format={
                    "container": "raw",
                    "encoding": "pcm_f32le",
                    "sample_rate": SAMPLE_RATE
                }
            ):
                if isinstance(chunk, bytes):
                    yield chunk
                elif hasattr(chunk, "audio") and chunk.audio:
                    yield chunk.audio


class CartesiaSTTProvider(STTProvider):
    """
    Cartesia STT Provider implementing STTProvider base class.
    Supports English (en), Hindi (hi), and Spanish (es).
    Uses Cartesia ink-whisper model.
    """

    def __init__(self, language: str = "en"):
        self.language = language
        self.api_key = os.getenv("CARTESIA_API_KEY")
        if not self.api_key:
            raise ValueError("CARTESIA_API_KEY not set in environment")

    async def transcribe_stream(
        self, audio_generator: AsyncGenerator[bytes, None]
    ) -> Dict[str, Any]:
        pcm_data = b""
        async for chunk in audio_generator:
            pcm_data += chunk

        wav_data = pcm_to_wav(pcm_data)

        client = Cartesia(api_key=self.api_key)
        response = client.stt.transcribe(
            file=("audio.wav", io.BytesIO(wav_data), "audio/wav"),
            model="ink-whisper",
            language=self.language,
        )

        return {
            "text": response.text,
            "language": response.language,
            "duration": response.duration
        }