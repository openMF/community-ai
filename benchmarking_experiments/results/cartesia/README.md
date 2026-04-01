# Cartesia Multilingual Evaluation — AI-168

## Overview
Benchmarks Cartesia's **sonic-2** (TTS) and **ink-whisper** (STT) models
across English (en), Hindi (hi), and Spanish (es).

## TTS Results

| Language | Avg Latency |
|----------|-------------|
| English  | 1618.15 ms  |
| Hindi    | 1773.22 ms  |
| Spanish  | 1331.39 ms  |

**Findings:**
- All 3 languages synthesized successfully with natural audio
- Spanish is fastest, Hindi is slowest
- Latency is acceptable for real-time use across all languages

## STT Results (Round-trip: TTS → STT)

| Language | Avg WER | Quality |
|----------|---------|---------|
| English  | 0.0     | ✅ Perfect |
| Spanish  | 0.0     | ✅ Perfect |
| Hindi    | 1.0476  | ⚠️ Poor |

> WER = Word Error Rate. 0.0 = perfect, 1.0 = completely wrong.

**Findings:**
- English and Spanish STT is flawless
- Hindi STT fails consistently — ink-whisper produces garbled output
- Hindi issue is likely due to model limitations with Devanagari script at 44100Hz

## Recommendations
1. English and Spanish are production-ready for both TTS and STT
2. Hindi TTS works well but STT needs a better model or lower sample rate (16000Hz)
3. Consider testing sonic-3 for improved Hindi TTS latency

## How to Run
```bash
pip install cartesia python-dotenv
# Add CARTESIA_API_KEY to .env
cd benchmarking_experiments
python tests/test_cartesia_multilingual.py
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