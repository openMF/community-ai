# Whisper.cpp Evaluation Setup (AI-167)

**Objective:** Evaluate multilingual STT support of smallest AI models for mobile/edge devices.

**Approach:** Use whisper.cpp (C/C++ optimized Whisper) instead of Python/HuggingFace transformers, because:
- Runs on iOS, Android, Raspberry Pi (not just servers)
- Lower latency and memory footprint
- Built-in benchmarking tools
- Quantization support for smaller models

This setup was collaboratively designed with Claude Opus 4.5 after analyzing:
- whisper.cpp architecture and existing benchmark utilities  
- community-ai repo structure
- Mobile performance requirements for AI-167
- Minimal PR approach (82 lines total, maximum clarity)

## Prerequisites

- macOS, Linux, or Windows
- `cmake` and `make`
- `python3`

## Setup

Initialize the whisper.cpp submodule:

```bash
cd evaluation
git submodule update --init
```

Build whisper.cpp:

```bash
cd whisper.cpp
cmake -B build
cmake --build build -j --config Release
cd ..
```

## Running Evaluations

To evaluate whisper-tiny, whisper-base, and whisper-small across multiple languages:

```bash
python run_multilingual_eval.py
```

This will:
1. Download models (tiny, base, small) in ggml format
2. Run benchmarks across 5 languages: English, Hindi, Spanish, French, German
3. Output results to `results/whisper_benchmarks.csv`

Results include: WER, CER, latency, model size, memory usage.
