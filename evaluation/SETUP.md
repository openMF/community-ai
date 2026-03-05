# Whisper.cpp Evaluation Setup (AI-167)

This folder contains evaluation infrastructure for measuring multilingual support of smallest AI models using whisper.cpp.

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
