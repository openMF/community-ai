# Faster Whisper Benchmark

This repository provides benchmarking utilities for the [faster-whisper](https://github.com/SYSTRAN/faster-whisper) model, profiling both encoder and decoder performance on various devices. It supports logging to Weights & Biases (wandb) and outputs results in a pandas table for easy analysis.

## Features
- Benchmarks Whisper encoder and decoder separately
- Logs detailed metrics (latency, memory, utilization, etc.)
- Supports multiple devices and model variants
- Outputs results as a pandas DataFrame
- Optional logging to wandb

## Setup

You must set up Qualcomm AI Hub and set up wandb if you want to log online.

**Important:** You must use PyTorch version 2.8.0. See [PyTorch previous versions](https://pytorch.org/get-started/previous-versions/).
Otherwise, decoder profiling will fail.
```

## Usage

Run the main benchmark script:

```bash
python main.py [--model_id MODEL_ID] [--batch_size N] [--decoder_len N] [--tokens N] [--feature_length N] [--wandb_project NAME] [--wandb_mode online|offline|disabled]
```

### Example

```bash
python main.py --model_id openai/whisper-small --batch_size 1 --feature_length 3000 --wandb_mode online
```

## Output
- Prints a summary table of encoder and decoder metrics using pandas
- Logs metrics to wandb if enabled
- Shows total estimated latency and combined memory usage

## File Structure
- `main.py` — Main benchmarking script
- `scripts/setup_env.py` — Environment and dependency setup
- `models/whisper_wrappers.py` — Model wrapper classes
- `utils/benchmark.py` — Torch utility functions
- `metrics/extractor.py` — Metric extraction and logging

## Customization
- Edit `devices_list` in `main.py` to benchmark on different devices
- Adjust arguments to benchmark different model sizes or input shapes

