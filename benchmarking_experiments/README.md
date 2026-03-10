# Speech Benchmarking

A benchmark suite designed to evaluate various speech-to-text (STT), text-to-speech (TTS), and speech-to-speech (STS) models

## Repository Structure

- `dataset/`: Contains the banking-first multilingual dataset and metadata.
- `providers/`: The core pattern implementing wrapper classes for each model.
- `metrics/`: Independent evaluation modules for accuracy (WER/CER), latency, and system tracking.
- `runners/`: Orchestration logic linking datasets, providers, and metrics.
- `results/`: Auto-generated outputs and benchmark matrices.
- `utils/`: Shared helpers for audio streaming, logging, etc.

## Getting Started

1. Set up a virtual environment and configure dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Make a copy of `.env.example` to `.env` and fill in your API keys.
3. Run the CLI tool:
   ```bash
   python cli.py --help
   ```
