import argparse
import asyncio
import os
from runners.benchmark_runner import BenchmarkRunner
from utils.helpers import load_env_vars

async def main():
    parser = argparse.ArgumentParser(description="Speech Benchmarking CLI")
    parser.add_argument("--provider", type=str, default="sarvam", help="Provider to use (default: sarvam)")
    parser.add_argument("--task", type=str, choices=["speech", "translate", "generate-dataset"], default="speech", help="Benchmark task")
    parser.add_argument("--dataset-id", type=str, default="dataset/metadata.json", help="HF Dataset ID or local path")
    parser.add_argument("--split", type=str, default="test", help="Dataset split to use (default: test)")
    parser.add_argument("--streaming", action="store_true", help="Use streaming mode for dataset loading")
    
    args = parser.parse_args()
    
    load_env_vars()
    
    if args.task == "generate-dataset":
        from dataset.generate_audio import generate_audio_dataset
        await generate_audio_dataset()
        return

    runner = BenchmarkRunner(provider_name=args.provider)
    
    if args.task == "speech":
        await runner.run_speech_benchmark(
            dataset_name=args.dataset_id, 
            split=args.split, 
            streaming=args.streaming
        )
    else:
        print(f"Task {args.task} not fully implemented in CLI yet.")

if __name__ == "__main__":
    asyncio.run(main())
