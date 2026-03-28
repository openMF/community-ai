import os
import json
import time
import asyncio
from datetime import datetime
from datasets import load_dataset, Audio
from providers.sarvam import SarvamProvider
from metrics.accuracy import (
    calculate_wer, 
    calculate_cer, 
    calculate_jaro_winkler, 
    calculate_semantic_similarity, 
    calculate_entity_accuracy
)
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class BenchmarkRunner:
    def __init__(self, provider_name="sarvam"):
        self.provider = SarvamProvider() if provider_name == "sarvam" else None
        self.results = []

    async def run_speech_benchmark(self, dataset_name, split="test", streaming=False):
        if not self.provider:
            logger.error("Provider not supported.")
            return

        logger.info(f"Loading dataset {dataset_name}...")
        try:
            # If dataset_name ends in .json, it's a local file, otherwise it's a HF dataset
            if dataset_name.endswith(".json"):
                ds = load_dataset("json", data_files=dataset_name, split="train")
            else:
                ds = load_dataset(dataset_name, split=split, streaming=streaming)
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            return

        logger.info(f"Benchmarking items...")
        
        for item in ds:
            # Handle potential variations in field names
            file_id = item.get("id", item.get("audio_path", "unknown"))
            lang_code = item.get("language_code", "hi")
            lang_name = item.get("language_name", "Hindi")
            text = item.get("text", item.get("sentence", ""))
            expected_entities = item.get("expected_entities", [])
            
            audio_data = item.get("audio")
            latency_tts = 0
            
            # audio_data can be a path or a dict from HF datasets
            audio_path = None
            if isinstance(audio_data, dict) and "path" in audio_data:
                audio_path = audio_data["path"]
            elif isinstance(audio_data, str):
                audio_path = audio_data
            
            # Generate audio if not pre-provided in the dataset
            if not audio_path or not os.path.exists(audio_path):
                # If 'audio' is a dict with 'array', we might need to save it to a temp file
                if isinstance(audio_data, dict) and "array" in audio_data:
                    import soundfile as sf
                    audio_path = f"results/temp_{file_id}.wav"
                    sf.write(audio_path, audio_data["array"], audio_data["sampling_rate"])
                else:
                    audio_path = f"results/temp_{file_id}.wav"
                    start = time.time()
                    if not self.provider.text_to_speech(text, lang_code, audio_path):
                        logger.error(f"TTS failed: {file_id}")
                        continue
                    latency_tts = time.time() - start

            # Transcribe
            start = time.time()
            hyp = self.provider.speech_to_text(audio_path, lang_code=lang_code)
            latency_stt = time.time() - start
            
            if not hyp:
                logger.error(f"STT failed: {file_id}")
                continue

            # Compute Metrics
            self.results.append({
                "id": file_id,
                "language": lang_name,
                "ref": text,
                "hyp": hyp,
                "wer": calculate_wer(text, hyp),
                "cer": calculate_cer(text, hyp),
                "jaro_winkler": calculate_jaro_winkler(text, hyp),
                "semantic_similarity": calculate_semantic_similarity(text, hyp),
                "entity_accuracy": calculate_entity_accuracy(hyp, expected_entities),
                "tts_latency": latency_tts,
                "stt_latency": latency_stt
            })
            
            # Temporary file cleanup
            if "temp_" in os.path.basename(audio_path) and os.path.exists(audio_path):
                os.remove(audio_path)

        self.save_results()

    def save_results(self):
        with open("results/benchmark_output.json", "w") as f:
            json.dump(self.results, f, indent=4)
        self._update_markdown_report()

    def _update_markdown_report(self):
        report_path = "results/RESULTS.md"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(report_path, "a", encoding="utf-8") as f:
            f.write(f"\n## Benchmark Run [{timestamp}]\n\n")
            f.write("| Lang | WER | CER | JW | Sem Sim | Ent Acc | Latency |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for r in self.results:
                f.write(f"| {r['language']} | {r['wer']:.3f} | {r['cer']:.3f} | {r['jaro_winkler']:.3f} | {r['semantic_similarity']:.3f} | {r['entity_accuracy']:.1%} | {r['stt_latency']:.2f}s |\n")
            
            if self.results:
                avg_sem = sum(r['semantic_similarity'] for r in self.results) / len(self.results)
                avg_ent = sum(r['entity_accuracy'] for r in self.results) / len(self.results)
                f.write(f"\n**Aggregates:** Semantic: **{avg_sem:.3f}**, Entity: **{avg_ent:.1%}**\n")
