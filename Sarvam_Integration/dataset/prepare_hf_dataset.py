import os
import json
import shutil
import pandas as pd
from datasets import Dataset, Audio, Features, Value

def prepare_hf_dataset(metadata_path="dataset/metadata.json", output_dir="hf_dataset_export"):
    """
    Converts the local dataset structure into a format compatible with Hugging Face datasets.
    """
    if not os.path.exists(metadata_path):
        print(f"Error: {metadata_path} not found.")
        return

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    data = []
    for item in metadata:
        # Resolve path relative to project root
        audio_path = os.path.abspath(item["audio_path"])
        if not os.path.exists(audio_path):
            print(f"Warning: Audio file not found for {item['id']}: {audio_path}")
            continue
            
        data.append({
            "id": item["id"],
            "language_name": item["language_name"],
            "language_code": item["language_code"],
            "text": item["text"],
            "expected_entities": item["expected_entities"],
            "audio": f"audio/{os.path.basename(audio_path)}"
        })

    # Create HF Dataset using paths (bypasses local torchcodec/encoding issues)
    features = Features({
        "id": Value("string"),
        "language_name": Value("string"),
        "language_code": Value("string"),
        "text": Value("string"),
        "expected_entities": [Value("string")],
        "audio": Value("string") # Store as path for portability
    })
    
    ds = Dataset.from_list(data, features=features)
    
    # Save to disk in a format ready for HF push
    os.makedirs(output_dir, exist_ok=True)
    # Save as JSONL for maximum compatibility
    ds.to_json(os.path.join(output_dir, "metadata.jsonl"), force_ascii=False)
    
    # Copy audio files into the export directory for the push
    audio_export_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_export_dir, exist_ok=True)
    for item in metadata:
        src = os.path.abspath(item["audio_path"])
        if os.path.exists(src):
            shutil.copy(src, audio_export_dir)

    print(f"Dataset prepared and saved to {output_dir}")
    print("The files have been exported as a JSONL + Audio folder structure.")
    print("To push to Hugging Face and enable the 'Audio' feature:")
    print(f"  huggingface-cli login")
    print(f"  python -c \"from datasets import load_dataset, Audio; ds = load_dataset('json', data_files='{output_dir}/metadata.jsonl'); ds = ds.cast_column('audio', Audio()); ds.push_to_hub('your-username/your-dataset-name')\"")

if __name__ == "__main__":
    prepare_hf_dataset()
