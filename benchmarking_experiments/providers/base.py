from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any

class STTProvider(ABC):
    """Abstract Base Class for Speech-to-Text Providers"""
    
    @abstractmethod
    async def transcribe_stream(self, audio_generator: AsyncGenerator[bytes, None]) -> Dict[str, Any]:
        """
        Takes an asynchronous generator of audio chunks and returns a transcription result.
        """
        pass

class TTSProvider(ABC):
    """Abstract Base Class for Text-to-Speech Providers"""
    
    @abstractmethod
    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Takes a string of text and yields chunks of synthesized audio.
        """
        pass

class STSProvider(ABC):
    """Abstract Base Class for Speech-to-Speech Providers"""
    
    @abstractmethod
    async def process_speech_stream(self, audio_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[bytes, None]:
        """
        Takes an asynchronous generator of audio chunks and yields chunks of response audio.
        """
        pass
