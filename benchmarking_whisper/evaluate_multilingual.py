import os
import time
import io
import pandas as pd
import torch
import librosa
import numpy as np
import psutil
from huggingface_hub import hf_hub_download, list_repo_files
from providers.hf_whisper import transcribe_hf
from results.metrics import calculate_wer, calculate_cer, calculate_bleu

# Configuration for the Whisper Benchmarking Suite
REPO_ID = "bhoomi16/mifos-banking-stt"

# Mapping language codes to Hub directories
DIR_MAPPING = {
    "en": "english_audio/",
    "hi": "hindi_audio/",
    "fr": "french_audio/",
    "es": "spanish_audio/",
    "pt": "portuguese_audio/"
}

MODELS = ["openai/whisper-small", "openai/whisper-small.en"]
LANGUAGES = ["hi", "en", "fr", "es", "pt"]

def run_benchmark_pass(model_name, lang_code):
    print(f"Benchmarking {model_name} - {lang_code}...")
    
    folder_prefix = DIR_MAPPING.get(lang_code, "english_audio/")
    
    try:
        remote_files = list_repo_files(repo_id=REPO_ID, repo_type="dataset")
        # Filter for audio files in the matching language folder
        target_files = [f for f in remote_files if f.startswith(folder_prefix) and f.endswith(".wav")]
        
        if not target_files:
            return []
            
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

    results = []
    pid = psutil.Process(os.getpid())
    
    # 📊 Now evaluating the FULL dataset for each language
    for file_path in target_files: 
        try:
            temp_local_file = hf_hub_download(repo_id=REPO_ID, filename=file_path, repo_type="dataset")
            audio, _ = librosa.load(temp_local_file, sr=16000)
            
            # Ground truth text from filename
            reference = str(file_path.split("/")[-1].replace(".wav", "").replace("_", " ")).lower()
            
            # Transcription cycle
            start = time.time()
            hypothesis, _ = transcribe_hf(audio, model_name=model_name, language=lang_code)
            latency = time.time() - start
            
            results.append({
                "Model": model_name,
                "Language": lang_code,
                "WER": calculate_wer(reference, hypothesis),
                "CER": calculate_cer(reference, hypothesis),
                "BLEU": calculate_bleu(reference, hypothesis),
                "Latency": latency,
                "Memory_MB": pid.memory_info().rss / (1024 * 1024)
            })
            
            if os.path.exists(temp_local_file): os.remove(temp_local_file)
            
        except Exception as e:
            print(f"Processing error ({file_path}): {e}")
            continue
    
    return results

def main():
    print("Mifos AI Whisper Benchmarking Suite (Portable Edition) - FULL RUN")
    print("-" * 65)
    
    consolidated_metrics = []
    
    for model in MODELS:
        # Only run Whisper-Small.en for English to save time and redundant compute
        for lang in LANGUAGES:
            if ".en" in model and lang != "en": continue
            data = run_benchmark_pass(model, lang)
            consolidated_metrics.extend(data)
            
    if consolidated_metrics:
        # Aggregation Logic
        df = pd.DataFrame(consolidated_metrics)
        final_summary = df.groupby(["Model", "Language"]).mean(numeric_only=True).reset_index()
        
        # Save to final results.md at root
        output_template = "# Whisper Benchmark Results (Full Dataset)\n\n"
        output_template += f"Cloud Data Source: {REPO_ID}\n"
        output_template += f"Total Samples Evaluated: {len(df)}\n\n"
        output_template += "### Performance Summary\n"
        output_template += final_summary.to_markdown(index=False)
        
        with open("results.md", "w", encoding="utf-8") as f:
            f.write(output_template)
            
        print(f"\nProcess finished. {len(df)} samples processed. Results available in results.md")

if __name__ == "__main__":
    main()
