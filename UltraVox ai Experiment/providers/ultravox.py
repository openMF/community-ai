import os, json, time, wave, asyncio
import aiohttp, websockets

BASE_URL = "https://api.ultravox.ai/api"
MODEL = "fixie-ai/ultravox"


class UltravoxProvider:
    SUPPORTED_LANGUAGES = ["en", "es", "fr", "hi", "bn", "ta", "te"]

    def __init__(self):
        self.api_key = os.getenv("ULTRAVOX_API_KEY")
        if not self.api_key:
            raise ValueError("ULTRAVOX_API_KEY required")
        self._session = None

    async def _session_open(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60),
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _create_call(self, language, sample_rate, system_prompt=None, first_speaker="FIRST_SPEAKER_USER"):
        session = await self._session_open()
        payload = {
            "systemPrompt": system_prompt or (
                "You are a helpful assistant. Repeat back exactly what the user says, word for word, "
                "in the same language. Do not add anything else."
            ),
            "model": MODEL,
            "languageHint": language,
            "firstSpeaker": first_speaker,
            "transcriptOptional": False,
            "maxDuration": "60s",
            "medium": {"serverWebSocket": {
                "inputSampleRate": sample_rate,
                "outputSampleRate": sample_rate,
            }},
        }
        async with session.post(f"{BASE_URL}/calls", json=payload) as r:
            if r.status == 402:
                raise RuntimeError("Quota exhausted or error occured.")
            if r.status not in (200, 201):
                raise RuntimeError(f"Call failed {r.status}: {await r.text()}")
            return (await r.json())["joinUrl"]

    @staticmethod
    def read_pcm(path):
        with wave.open(str(path), "rb") as w:
            return w.readframes(w.getnframes()), w.getframerate()

    async def transcribe(self, audio_path, language):
        pcm, sr = self.read_pcm(audio_path)
        start = time.perf_counter()
        join_url = await self._create_call(language, sr)

        async with websockets.connect(join_url) as ws:
            # Wait until Ultravox is ready to receive audio
            async with asyncio.timeout(10):
                async for msg in ws:
                    if isinstance(msg, str) and json.loads(msg).get("state") == "listening":
                        break

            # Stream audio in 20ms PCM16 chunks
            chunk = sr * 2 * 20 // 1000
            for i in range(0, len(pcm), chunk):
                await ws.send(pcm[i : i + chunk])
                await asyncio.sleep(0.02)
            # Send 1s silence so VAD detects end-of-speech
            await ws.send(b"\x00" * (sr * 2))

            # Collect transcript: prefer user transcript, fall back to agent echo
            user_transcript = ""
            agent_transcript = ""
            async with asyncio.timeout(30):
                async for msg in ws:
                    if isinstance(msg, bytes):
                        continue
                    evt = json.loads(msg)
                    if evt.get("type") == "transcript" and evt.get("final"):
                        if evt.get("role") == "user":
                            user_transcript = evt.get("text", "")
                            break
                        if evt.get("role") == "agent":
                            agent_transcript = evt.get("text", "").strip()
                    # Agent done, back to listening — use what we have
                    if evt.get("type") == "state" and evt.get("state") == "listening":
                        if agent_transcript:
                            break
                    if evt.get("type") in ("call_ended", "hang_up", "error"):
                        break

        transcript = user_transcript or agent_transcript

        latency_ms = (time.perf_counter() - start) * 1000
        if not transcript:
            raise RuntimeError("No transcript received from Ultravox")
        return transcript, latency_ms

    async def measure_ttfa(self, audio_path, language):
        """Measure Time to First Audio — ms from end of user audio to first agent audio byte."""
        pcm, sr = self.read_pcm(audio_path)
        join_url = await self._create_call(language, sr)

        async with websockets.connect(join_url) as ws:
            async with asyncio.timeout(10):
                async for msg in ws:
                    if isinstance(msg, str) and json.loads(msg).get("state") == "listening":
                        break

            chunk = sr * 2 * 20 // 1000
            for i in range(0, len(pcm), chunk):
                await ws.send(pcm[i : i + chunk])
                await asyncio.sleep(0.02)
            await ws.send(b"\x00" * (sr * 2))
            audio_sent_at = time.perf_counter()

            # Wait for first audio byte back from agent
            async with asyncio.timeout(30):
                async for msg in ws:
                    if isinstance(msg, bytes):
                        ttfa_ms = (time.perf_counter() - audio_sent_at) * 1000
                        return ttfa_ms
                    evt = json.loads(msg)
                    if evt.get("type") in ("call_ended", "hang_up", "error"):
                        raise RuntimeError(f"Call ended before agent audio: {evt}")

        raise RuntimeError("No agent audio received")

    async def synthesize(self, text, language, sample_rate=24000):
        """TTS: send text, measure TTFA and total time until audio stream ends."""
        prompt = f"Say the following text out loud exactly as written, in {language}: {text}"
        join_url = await self._create_call(language, sample_rate, system_prompt=prompt,
                                           first_speaker="FIRST_SPEAKER_AGENT")
        start = time.perf_counter()
        first_byte_at = None
        audio_bytes = 0

        async with websockets.connect(join_url) as ws:
            async with asyncio.timeout(30):
                async for msg in ws:
                    if isinstance(msg, bytes):
                        if first_byte_at is None:
                            first_byte_at = time.perf_counter()
                        audio_bytes += len(msg)
                    elif isinstance(msg, str):
                        evt = json.loads(msg)
                        # Agent finished speaking → back to listening
                        if evt.get("type") == "state" and evt.get("state") == "listening" and first_byte_at:
                            break
                        if evt.get("type") in ("call_ended", "hang_up", "error"):
                            break

        if first_byte_at is None:
            raise RuntimeError("No audio received from Ultravox TTS")

        ttfa_ms = (first_byte_at - start) * 1000
        total_ms = (time.perf_counter() - start) * 1000
        return ttfa_ms, total_ms, audio_bytes
