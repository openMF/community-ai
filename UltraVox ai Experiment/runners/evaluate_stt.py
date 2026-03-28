import json
from pathlib import Path
from weakref import ref
from metrics.accuracy import calculate_wer, calculate_cer
import utils

async def run_stt(provider, langs, dataset_dir):
    evaluator = STTEvaluator(provider, dataset_dir)
    await evaluator.run(langs)
    evaluator.save()

class STTEvaluator:
    def __init__(self, provider, dataset_dir="mifos_audio_benchmarking"):
        self.provider = provider
        metadata_path = Path(dataset_dir) / "metadata.json"
        self.dataset = json.loads(metadata_path.read_text())
        self.dataset_dir = Path(dataset_dir)
        self.results = []

    async def run(self, languages):
        for lang in languages:
            for s in self.dataset["languages"][lang]["samples"]:
                speech_id, reference = s["id"], s["reference_text"]
                audio = str(self.dataset_dir / s["audio_path"])

                result, latency = await self.provider.transcribe(audio, lang)
                
                wer = calculate_wer(reference, result, lang)
                cer = calculate_cer(reference, result, lang)
                acc = max(0.0, 1.0 - wer) * 100

                self.results.append(
                    dict(
                        lang=lang,
                        id=speech_id,
                        wer=wer,
                        cer=cer,
                        accuracy=acc,
                        latency_ms=round(latency, 1), 
                        reference=reference, 
                        hypothesis=result)
                    )
                
                print(f"\n{'='*60}")
                print(f"{'Lang':<6}{'Sample':<15}{'WER':<9}{'CER':<9}{'Accuracy':<11}{'Latency(ms)':<13}{'Status'}")
                print("=" * 60)
                print(f"{lang:<6}{speech_id:<15}{wer:<9.4f}{cer:<9.4f}{acc:<10.1f}% {latency:<12.0f} OK")
                print(f"Reference Text: {reference}")
                print(f"Transcribed Text: {result}")
                print() 
                print()

                
    def save(self, path="results/stt_benchmark.json"):
        utils.save_json(self.results, path)

