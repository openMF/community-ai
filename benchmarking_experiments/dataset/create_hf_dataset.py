"""
HuggingFace Dataset Builder for Mifos Speech Benchmarking (AI-172)

Creates a multilingual STT benchmarking dataset with:
- Audio samples in Hindi, French, Portuguese (+ English baseline)
- Ground truth transcriptions
- Financial domain metadata
- HuggingFace-compatible format for community reuse

Dataset structure:
  mifos-speech-benchmark/
  ├── dataset_card.md
  ├── metadata.csv
  └── audio/
      ├── hi/  (Hindi samples)
      ├── fr/  (French samples)
      ├── pt/  (Portuguese samples)
      └── en/  (English baseline)

Usage:
  python create_hf_dataset.py --output ./mifos-speech-benchmark
  python create_hf_dataset.py --upload --repo mifos/speech-benchmark
"""

import os
import csv
import json
import argparse

# Ground truth transcriptions per language
# These are financial domain sentences for Mifos use cases
GROUND_TRUTH = {
    "en": [
        {"id": "en_001", "text": "I would like to open a savings account", "domain": "account_opening"},
        {"id": "en_002", "text": "What is my current account balance", "domain": "balance_inquiry"},
        {"id": "en_003", "text": "I need to transfer five thousand to another account", "domain": "money_transfer"},
        {"id": "en_004", "text": "Can you show me my recent transactions", "domain": "transaction_history"},
        {"id": "en_005", "text": "I want to apply for a personal loan", "domain": "loan_inquiry"},
    ],
    "hi": [
        {"id": "hi_001", "text": "मैं एक बचत खाता खोलना चाहता हूं", "domain": "account_opening"},
        {"id": "hi_002", "text": "मेरा वर्तमान खाता शेष क्या है", "domain": "balance_inquiry"},
        {"id": "hi_003", "text": "मुझे पांच हजार दूसरे खाते में भेजने हैं", "domain": "money_transfer"},
        {"id": "hi_004", "text": "मेरे हाल के लेनदेन दिखाइए", "domain": "transaction_history"},
        {"id": "hi_005", "text": "मैं व्यक्तिगत ऋण के लिए आवेदन करना चाहता हूं", "domain": "loan_inquiry"},
    ],
    "fr": [
        {"id": "fr_001", "text": "Je voudrais ouvrir un compte épargne", "domain": "account_opening"},
        {"id": "fr_002", "text": "Quel est le solde actuel de mon compte", "domain": "balance_inquiry"},
        {"id": "fr_003", "text": "Je dois transférer cinq mille vers un autre compte", "domain": "money_transfer"},
        {"id": "fr_004", "text": "Pouvez-vous me montrer mes transactions récentes", "domain": "transaction_history"},
        {"id": "fr_005", "text": "Je veux demander un prêt personnel", "domain": "loan_inquiry"},
    ],
    "pt": [
        {"id": "pt_001", "text": "Gostaria de abrir uma conta poupança", "domain": "account_opening"},
        {"id": "pt_002", "text": "Qual é o saldo atual da minha conta", "domain": "balance_inquiry"},
        {"id": "pt_003", "text": "Preciso transferir cinco mil para outra conta", "domain": "money_transfer"},
        {"id": "pt_004", "text": "Pode mostrar as minhas transações recentes", "domain": "transaction_history"},
        {"id": "pt_005", "text": "Quero solicitar um empréstimo pessoal", "domain": "loan_inquiry"},
    ],
}

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "fr": "French", "pt": "Portuguese"}


def create_dataset_structure(output_dir: str):
    """Create HuggingFace-compatible dataset directory structure"""

    # Create audio directories per language
    for lang in GROUND_TRUTH:
        os.makedirs(os.path.join(output_dir, "audio", lang), exist_ok=True)

    # Write metadata.csv (HuggingFace datasets format)
    metadata_path = os.path.join(output_dir, "metadata.csv")
    with open(metadata_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "file_name", "transcription", "language", "language_name",
            "domain", "sample_id", "duration_seconds"
        ])
        writer.writeheader()

        for lang, samples in GROUND_TRUTH.items():
            for sample in samples:
                writer.writerow({
                    "file_name": f"audio/{lang}/{sample['id']}.wav",
                    "transcription": sample["text"],
                    "language": lang,
                    "language_name": LANGUAGE_NAMES[lang],
                    "domain": sample["domain"],
                    "sample_id": sample["id"],
                    "duration_seconds": "",  # To be filled after audio recording
                })

    print(f"✅ metadata.csv created at {metadata_path}")
    print(f"   {sum(len(s) for s in GROUND_TRUTH.values())} samples across {len(GROUND_TRUTH)} languages")

    # Write ground truth JSON (for programmatic access)
    gt_path = os.path.join(output_dir, "ground_truth.json")
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(GROUND_TRUTH, f, ensure_ascii=False, indent=2)

    print(f"✅ ground_truth.json created at {gt_path}")

    return metadata_path


def create_dataset_card(output_dir: str):
    """Create HuggingFace dataset card (README.md)"""

    card = """---
language:
  - en
  - hi
  - fr
  - pt
task_categories:
  - automatic-speech-recognition
tags:
  - mifos
  - financial-inclusion
  - multilingual
  - speech-benchmark
  - gsoc-2026
pretty_name: Mifos Speech Benchmark
size_categories:
  - n<1K
---

# Mifos Speech Benchmark Dataset

Multilingual STT benchmarking dataset for financial inclusion use cases.

## Languages
| Code | Language   | Samples | Domain          |
|------|------------|---------|-----------------|
| en   | English    | 5       | Financial       |
| hi   | Hindi      | 5       | Financial       |
| fr   | French     | 5       | Financial       |
| pt   | Portuguese | 5       | Financial       |

## Domains
- Account opening
- Balance inquiry
- Money transfer
- Transaction history
- Loan inquiry

## Usage

```python
from datasets import load_dataset
dataset = load_dataset("mifos/speech-benchmark")
```

## Purpose
Built for evaluating STT providers (Deepgram, Whisper, Google, etc.)
across languages commonly used in Mifos financial inclusion applications.

## Contributing
To add more languages or samples, see the ground_truth.json file.
Audio samples should be 16kHz mono WAV files.
"""
    card_path = os.path.join(output_dir, "README.md")
    with open(card_path, "w") as f:
        f.write(card)

    print(f"✅ Dataset card created at {card_path}")


def upload_to_huggingface(dataset_dir: str, repo_id: str):
    """Upload dataset to HuggingFace Hub"""
    try:
        from huggingface_hub import HfApi

        api = HfApi()
        api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
        api.upload_folder(
            folder_path=dataset_dir,
            repo_id=repo_id,
            repo_type="dataset",
        )
        print(f"✅ Dataset uploaded to https://huggingface.co/datasets/{repo_id}")

    except ImportError:
        print("❌ Install huggingface_hub: pip install huggingface_hub")
    except Exception as e:
        print(f"❌ Upload failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Mifos Speech Benchmark Dataset")
    parser.add_argument("--output", default="./dataset/mifos-speech-benchmark", help="Output directory")
    parser.add_argument("--upload", action="store_true", help="Upload to HuggingFace")
    parser.add_argument("--repo", default="mifos/speech-benchmark", help="HuggingFace repo ID")

    args = parser.parse_args()

    create_dataset_structure(args.output)
    create_dataset_card(args.output)

    if args.upload:
        upload_to_huggingface(args.output, args.repo)
    else:
        print(f"\nTo upload: python create_hf_dataset.py --upload --repo {args.repo}")
