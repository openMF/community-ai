# Ultravox Multilingual Speech Benchmarking

Evaluation suite for benchmarking **Ultravox AI** across Speech-to-Text (STT), Speech-to-Speech (STS), and Text-to-Speech (TTS) using a multilingual banking domain dataset.

## Metrics

| Mode | Metrics |
|------|---------|
| **STT** | WER, CER, accuracy (%), latency (ms) |
| **STS** | TTFA — Time to First Audio (ms) |
| **TTS** | TTFA (ms), total synthesis time (ms), audio bytes |

## Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `es` | Spanish |
| `hi` | Hindi |
| `bn` | Bengali |
| `fr` | French |
| `ta` | Tamil |
| `te` | Telugu |

Each language has 3 banking-domain audio samples (24 kHz, 16-bit mono WAV).

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
ULTRAVOX_API_KEY=your_api_key_here
```

## Usage

```bash
# STT — transcription accuracy
python run_ultravox.py --mode stt --language en

# STS — time to first audio (speech-in → speech-out)
python run_ultravox.py --mode sts --language en

# TTS — synthesis latency
python run_ultravox.py --mode tts --language en

# Run all modes
python run_ultravox.py --mode all --language en
```

`--mode` choices: `stt`, `sts`, `tts`, `all` (default: `sts`)
`--language` choices: `bn`, `en`, `es`, `fr`, `hi`, `ta`, `te` (default: `en`)

## Project Structure

```
benchmarking_experiments/
├── run_ultravox.py              # CLI entry point (argparse)
├── requirements.txt             # Python dependencies
├── providers/
│   └── ultravox.py              # Ultravox WebSocket provider
├── runners/
│   ├── evaluate_stt.py          # STT evaluator (WER/CER/accuracy/latency)
│   ├── evaluate_sts.py          # STS evaluator (TTFA)
│   └── evaluate_tts.py          # TTS evaluator (TTFA/total time)
├── metrics/
│   └── accuracy.py              # WER & CER via jiwer + multilingual normalize
├── utils/
│   └── save_json.py             # JSON result writer
└── results/                     # Auto-generated benchmark JSON outputs
```

## How It Works

The provider creates an Ultravox call via `POST https://api.ultravox.ai/api/calls`, then connects to the returned WebSocket URL.

- **STT**: Streams audio as PCM16 binary frames, sends 1 s of silence for VAD end-of-speech detection, then collects the transcript (user transcript preferred, agent echo as fallback).
- **STS**: Same as STT audio streaming, but measures time from end of audio send to first agent audio byte received.
- **TTS**: Creates a call with `FIRST_SPEAKER_AGENT` and a prompt containing the text to synthesize. Measures time to first audio byte and total synthesis duration.

## Results

Results are saved as JSON arrays in `results/`:

- `results/stt_benchmark.json` — per-sample WER, CER, accuracy, latency, reference, hypothesis
- `results/sts_benchmark.json` — per-sample TTFA
- `results/tts_benchmark.json` — per-sample TTFA, total time, audio bytes, input text

## Dependencies

- `aiohttp` — HTTP client for Ultravox REST API
- `websockets` — WebSocket connection to Ultravox calls
- `jiwer` — WER/CER computation
- `python-dotenv` — `.env` file loading

