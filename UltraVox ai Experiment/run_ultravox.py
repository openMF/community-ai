#!/usr/bin/env python3
"""Ultravox Benchmark — STT (WER/CER/accuracy/latency) and STS (TTFA)."""

import asyncio, argparse
from dotenv import load_dotenv
from providers import UltravoxProvider
from runners import STTEvaluator, STSEvaluator, TTSEvaluator
from runners.evaluate_stt import run_stt 
from runners.evaluate_sts import run_sts
from runners.evaluate_tts import run_tts
from huggingface_hub import snapshot_download


load_dotenv()

parser = argparse.ArgumentParser(description="Ultravox Speech Benchmark")
parser.add_argument('--mode', default='all', choices=['stt', 'sts', 'tts', 'all'], help="Evaluation mode to run")
parser.add_argument('--language', default=['en'],choices=['bn', 'en', 'es', 'fr', 'hi', 'ta', 'te'], help="Languages to evaluate (default: en)")

args = parser.parse_args()

async def main():
    local_dir = snapshot_download(repo_id="itsPronay/mifos_audio_benchmarking", repo_type="dataset")
    provider = UltravoxProvider()
    try:
        if args.mode == 'stt':
            await run_stt(provider, args.language, local_dir)
        elif args.mode == 'sts':
            await run_sts(provider, args.language, local_dir)
        elif args.mode == 'tts':
            await run_tts(provider, args.language, local_dir)
        elif args.mode == 'all':
            await run_stt(provider, args.language, local_dir)
            await run_sts(provider, args.language, local_dir)
            await run_tts(provider, args.language, local_dir)
    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())
