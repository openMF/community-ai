# benchmarking_experiments/tests/test_cartesia_multilingual.py

import asyncio
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

from providers.cartesia import CartesiaTTSProvider, CartesiaSTTProvider

TEST_SENTENCES = {
    "en": [
        "Hello, how can I help you today?",
        "Please transfer funds to the specified account.",
        "Your transaction has been processed successfully.",
    ],
    "hi": [
        "नमस्ते, मैं आपकी कैसे मदद कर सकता हूँ?",
        "कृपया निर्दिष्ट खाते में धनराशि स्थानांतरित करें।",
        "आपका लेन-देन सफलतापूर्वक संसाधित किया गया है।",
    ],
    "es": [
        "Hola, ¿cómo puedo ayudarte hoy?",
        "Por favor, transfiera fondos a la cuenta especificada.",
        "Su transacción ha sido procesada exitosamente.",
    ],
}

RESULTS_DIR = Path(__file__).parent.parent / "results" / "cartesia"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_wer(reference: str, hypothesis: str) -> float:
    ref = reference.lower().split()
    hyp = hypothesis.lower().split()
    d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for i in range(len(ref) + 1):
        d[i][0] = i
    for j in range(len(hyp) + 1):
        d[0][j] = j
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + cost)
    return round(d[len(ref)][len(hyp)] / max(len(ref), 1), 4)


async def collect_tts_audio(provider, text: str):
    chunks = []
    start = time.time()
    async for chunk in provider.synthesize_stream(text):
        chunks.append(chunk)
    latency_ms = round((time.time() - start) * 1000, 2)
    return b"".join(chunks), latency_ms


async def bytes_to_async_gen(data: bytes):
    chunk_size = 4096
    for i in range(0, len(data), chunk_size):
        yield data[i: i + chunk_size]
        await asyncio.sleep(0)


async def run_tts_benchmark():
    print("\n========== CARTESIA TTS BENCHMARK ==========")
    all_results = []

    for lang, sentences in TEST_SENTENCES.items():
        provider = CartesiaTTSProvider(language=lang)
        lang_results = []
        print(f"\n[TTS] Language: {lang.upper()}")

        for i, sentence in enumerate(sentences):
            audio_bytes, latency_ms = await collect_tts_audio(provider, sentence)
            record = {
                "text": sentence,
                "latency_ms": latency_ms,
                "audio_size_bytes": len(audio_bytes),
                "language": lang,
                "model": "sonic-2",
            }
            lang_results.append(record)
            print(f"  [{i+1}] latency={latency_ms}ms | size={len(audio_bytes)}b | {sentence[:45]}")

        avg_latency = round(sum(r["latency_ms"] for r in lang_results) / len(lang_results), 2)
        summary = {
            "language": lang,
            "avg_latency_ms": avg_latency,
            "total_samples": len(lang_results),
            "samples": lang_results,
        }
        all_results.append(summary)

        out = RESULTS_DIR / f"tts_{lang}_results.json"
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  → Avg latency: {avg_latency}ms | Saved: {out.name}")

    return all_results


async def run_stt_benchmark():
    print("\n========== CARTESIA STT BENCHMARK (round-trip) ==========")
    all_results = []

    for lang, sentences in TEST_SENTENCES.items():
        tts = CartesiaTTSProvider(language=lang)
        stt = CartesiaSTTProvider(language=lang)
        lang_results = []
        print(f"\n[STT] Language: {lang.upper()}")

        for i, sentence in enumerate(sentences):
            audio_bytes, _ = await collect_tts_audio(tts, sentence)

            start = time.time()
            stt_result = await stt.transcribe_stream(bytes_to_async_gen(audio_bytes))
            stt_result["latency_ms"] = round((time.time() - start) * 1000, 2)

            wer = compute_wer(sentence, stt_result.get("text", ""))
            stt_result["reference"] = sentence
            stt_result["wer"] = wer

            lang_results.append(stt_result)
            print(f"  [{i+1}] WER={wer} | latency={stt_result['latency_ms']}ms")
            print(f"       REF: {sentence}")
            print(f"       HYP: {stt_result.get('text', '')}")

        avg_wer = round(sum(r["wer"] for r in lang_results) / len(lang_results), 4)
        avg_lat = round(sum(r["latency_ms"] for r in lang_results) / len(lang_results), 2)
        summary = {
            "language": lang,
            "avg_wer": avg_wer,
            "avg_latency_ms": avg_lat,
            "total_samples": len(lang_results),
            "samples": lang_results,
        }
        all_results.append(summary)

        out = RESULTS_DIR / f"stt_{lang}_results.json"
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  → Avg WER: {avg_wer} | Avg latency: {avg_lat}ms | Saved: {out.name}")

    return all_results


async def main():
    tts_results = await run_tts_benchmark()
    stt_results = await run_stt_benchmark()

    print("\n========== FINAL SUMMARY ==========")
    for r in tts_results:
        print(f"TTS [{r['language'].upper()}]  avg latency : {r['avg_latency_ms']} ms")
    for r in stt_results:
        print(f"STT [{r['language'].upper()}]  avg WER     : {r['avg_wer']}  |  avg latency : {r['avg_latency_ms']} ms")
    print("\nAll results saved to: benchmarking_experiments/results/cartesia/")


if __name__ == "__main__":
    asyncio.run(main())