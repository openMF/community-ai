#!/usr/bin/env python3
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

cmd = ["python3", bench_script, "-p", "1", "-t", "4"]

try:
    subprocess.run(cmd, cwd=whisper_dir, check=True)
    print("✅ Benchmark complete!")
except subprocess.CalledProcessError as e:
    print(f"❌ Benchmark failed: {e}")
    sys.exit(1)
