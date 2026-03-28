# Speech Benchmarking

A benchmark suite designed to evaluate various speech-to-text (STT), text-to-speech (TTS), and speech-to-speech (STS) models.

## Repository Structure

- `dataset/`: Contains the banking-first multilingual dataset and metadata.
- `providers/`: The core pattern implementing wrapper classes for each model.
- `metrics/`: Independent evaluation modules for accuracy (WER/CER), latency, and system tracking.
- `runners/`: Orchestration logic linking datasets, providers, and metrics.
- `results/`: Auto-generated outputs and benchmark matrices.
- `utils/`: Shared helpers for audio streaming, logging, etc.

## Getting Started

1. **Set up a virtual environment and configure dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Make a copy of `.env.example` to `.env` and fill in your `SARVAM_API_KEY`.
   ```bash
   cp .env.example .env
   ```

3. **Run the CLI tool**:
   ```bash
   python cli.py --help
   ```

## Hugging Face Integration 🚀

This suite is fully integrated with the Hugging Face `datasets` library, allowing for scalable, remote evaluation without storing large audio files locally.

### 1. Remote Benchmarking
Run benchmarks directly from the Hugging Face Hub using the following flags:
- `--dataset-id`: The HF Dataset ID (e.g., `username/repo`).
- `--streaming`: (Recommended) Loads the dataset on-the-fly without downloading it to disk.
- `--split`: Choose the dataset split (default: `test`).

```bash
python cli.py --task speech --dataset-id "mozilla-foundation/common_voice_11_0" --split validation --streaming
```

### 2. Scalable Evaluation Utility
If you have local data, use the migration utility to package it for Hugging Face:
```bash
# Convert local metadata/audio to HF format
python dataset/prepare_hf_dataset.py

# The script will provide instructions to push the resulting folder to the HF Hub:
huggingface-cli login
python -c "from datasets import load_from_disk; ds = load_from_disk('hf_dataset_export'); ds.push_to_hub('your-username/dataset-name')"
```

## Usage

### Run Speech Benchmark
The CLI supports both local and remote datasets:
```bash
# Using a remote HF dataset (Recommended)
python cli.py --task speech --dataset-id "your-username/your-dataset" --streaming

# Using a local metadata.json file
python cli.py --task speech --dataset-id "dataset/metadata.json"
```

### Legacy: Local Audio Generation
If you want to generate local audio files from localized text before migrating to HF:
```bash
python cli.py --task generate-dataset
```

## Metrics
- **WER / CER**: Word/Character Error Rate for transcription accuracy.
- **Semantic Similarity**: Measures how closely the transcription preserves the meaning.
- **Entity Accuracy**: Tracks if critical entities (names, amounts) are preserved.
- **E2E Latency**: Tracks both TTS synthesis and STT transcription timing.
