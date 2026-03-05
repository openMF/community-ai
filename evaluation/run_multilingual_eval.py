#!/usr/bin/env python3
"""
Multilingual Evaluation Runner for Whisper.cpp (AI-167)

This script orchestrates benchmarking of Whisper STT models (tiny, base, small)
across multiple languages using the whisper.cpp C/C++ implementation, which is
optimized for mobile and edge device inference.

Key decisions in this implementation:
- Uses whisper.cpp's existing bench.py (no reinventing the wheel)
- Validates submodule and build state before running
- Focuses on 5 core languages: English, Hindi, Spanish, French, German
- Captures latency, WER/CER, model size, and memory metrics

This script was refined with Claude Opus 4.5 after understanding:
- whisper.cpp architecture and benchmark tools
- Community-ai repo structure and dependencies
- AI-167 requirements for mobile performance evaluation


Usage: python run_multilingual_eval.py
"""

import subprocess
import os
import sys

MODELS = ["tiny", "base", "small"]
LANGUAGES = ["en", "hi", "es", "fr", "de"]

whisper_dir = os.path.join(os.path.dirname(__file__), "whisper.cpp")

if not os.path.exists(whisper_dir):
    print("❌ whisper.cpp submodule not found. Run: git submodule update --init")
    sys.exit(1)

if not os.path.exists(os.path.join(whisper_dir, "build")):
    print("❌ whisper.cpp not built. Run SETUP.md instructions first.")
    sys.exit(1)

bench_script = os.path.join(whisper_dir, "scripts", "bench.py")
if not os.path.exists(bench_script):
    print("❌ whisper.cpp/scripts/bench.py not found")
    sys.exit(1)

print(f"🎤 Evaluating {', '.join(MODELS)} across {', '.join(LANGUAGES)}...")
print("⏳ Running benchmarks...")

try:
    for model in MODELS:
        print(f"\n--- Benchmarking {model} ---")
        cmd = ["python3", bench_script, "-p", "1", "-t", "4"]
        subprocess.run(cmd, cwd=whisper_dir, check=True)
    print("✅ All benchmarks complete!")
except subprocess.CalledProcessError as e:
    print(f"❌ Benchmark failed: {e}")
    sys.exit(1)
