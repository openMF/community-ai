"""
Deepgram STT Provider - Foundation for AI-172

Minimal implementation focused on:
1. Streaming transcription with multilingual support
2. Clean error handling
3. Standard metrics extraction for WER/CER calculation
"""

from typing import AsyncGenerator, Dict, Any, Optional
from .base import STTProvider


class DeepgramSTTProvider(STTProvider):
    """
    Deepgram Speech-to-Text Provider
    
    Required for AI-172: Evaluate multilingual support for Deepgram
    
    Supports: 50+ languages including low-resource (Swahili, Hindi)
    Models: Nova-2 (recommended), Enhanced, Base
    """
    
    SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "pt", "it", "hi", "sw", "ar", "ja", "ko", "zh"]
    
    def __init__(self, api_key: str, model: str = "nova-2", **kwargs):
        self.api_key = api_key
        self.model = model
        self.extra_options = kwargs
    
    async def transcribe_stream(
        self, 
        audio_generator: AsyncGenerator[bytes, None],
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio stream from Deepgram
        
        Returns dict with:
        - transcript: Full text output
        - confidence: Average confidence (0-1)
        - language: Detected or specified language
        - error: If transcription failed
        """
        try:
            from deepgram import DeepgramClient, PrerecordedOptions
            
            # Collect audio chunks efficiently (avoid O(n²) bytes concat)
            chunks = []
            async for chunk in audio_generator:
                chunks.append(chunk)
            audio_buffer = b"".join(chunks)
            
            if not audio_buffer:
                return {
                    "success": False,
                    "error": "No audio data",
                    "transcript": "",
                    "confidence": 0.0,
                    "language": language or "unknown"
                }
            
            # Initialize client and transcribe
            client = DeepgramClient(api_key=self.api_key)
            options = PrerecordedOptions(
                model=self.model,
                language=language,
                punctuate=True,
                **self.extra_options
            )
            
            response = await client.listen.prerecorded.v("1").transcribe_async(
                {"buffer": audio_buffer},
                options
            )
            
            # Convert SDK response object to dict for parsing
            if hasattr(response, "to_dict"):
                response = response.to_dict()
            elif hasattr(response, "model_dump"):
                response = response.model_dump()
            
            return self._parse_response(response, language)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "transcript": "",
                "confidence": 0.0,
                "language": language or "unknown"
            }
    
    def _parse_response(self, response: Dict[str, Any], language: Optional[str]) -> Dict[str, Any]:
        """Extract transcript and confidence from Deepgram response"""
        try:
            channel = response.get("results", {}).get("channels", [{}])[0]
            alternative = channel.get("alternatives", [{}])[0]
            
            return {
                "success": True,
                "transcript": alternative.get("transcript", ""),
                "confidence": alternative.get("confidence", 0.0),
                "language": language or "unknown",
                "model": self.model,
                "word_count": len(alternative.get("transcript", "").split())
            }
        except (IndexError, KeyError, AttributeError):
            return {
                "success": False,
                "error": "Failed to parse response",
                "transcript": "",
                "confidence": 0.0,
                "language": language or "unknown"
            }
