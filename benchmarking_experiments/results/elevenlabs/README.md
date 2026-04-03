# ElevenLabs Multilingual Evaluation

## Overview
Benchmarks ElevenLabs **Flash v2.5** (TTS) and **Scribe v1** (STT) models
across English (en), Hindi (hi), and Spanish (es).

## TTS Results

| Language | Avg Latency |
|----------|-------------|
| English  | 1762.63 ms  |
| Hindi    | 647.62 ms   |
| Spanish  | 682.80 ms   |

**Findings:**
- Hindi and Spanish TTS is significantly faster than English
- All 3 languages produce natural sounding audio
- Flash v2.5 model optimized for low latency multilingual output

## STT Results (Round-trip: TTS → STT)

| Language | Avg WER | Quality |
|----------|---------|---------|
| English  | 0.0     | ✅ Perfect |
| Hindi    | 0.089   | ✅ Very Good |
| Spanish  | 0.0     | ✅ Perfect |

**Findings:**
- English and Spanish STT is flawless (WER 0.0)
- Hindi STT performs very well (WER 0.089) — only minor punctuation
  differences observed (e.g. "हूँ" vs "हूं")
- Massive improvement over Cartesia's Hindi STT (WER 1.04 → 0.089)

## Comparison with Cartesia

| Metric | Cartesia | ElevenLabs | Improvement |
|--------|----------|------------|-------------|
| Hindi STT WER | 1.04 ⚠️ | 0.089 ✅ | 91% better |
| Hindi TTS Latency | 1773ms | 647ms | 63% faster |
| EN STT WER | 0.0 | 0.0 | Same |
| ES STT WER | 0.0 | 0.0 | Same |

## Key Finding
ElevenLabs Scribe v1 handles Hindi significantly better than
Cartesia's ink-whisper model. The minor WER (0.089) is due to
punctuation variants in Devanagari script, not actual word errors.

## How to Run
```bash
pip install elevenlabs python-dotenv
# Add ELEVENLABS_API_KEY to .env
cd benchmarking_experiments
python tests/test_elevenlabs_multilingual.py
```

## Files
| File | Description |
|------|-------------|
| `tts_en_results.json` | English TTS results |
| `tts_hi_results.json` | Hindi TTS results |
| `tts_es_results.json` | Spanish TTS results |
| `stt_en_results.json` | English STT results |
| `stt_hi_results.json` | Hindi STT results |
| `stt_es_results.json` | Spanish STT results |