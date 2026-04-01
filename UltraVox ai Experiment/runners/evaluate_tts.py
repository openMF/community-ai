import json
from pathlib import Path
import utils

async def run_tts(provider, langs, dataset_dir):
    evaluator = TTSEvaluator(provider, dataset_dir)
    await evaluator.run(langs)
    evaluator.save()

class TTSEvaluator:
    def __init__(self, provider, dataset_dir="mifos_audio_benchmarking"):
        self.provider = provider
        metadata_path = Path(dataset_dir) / "metadata.json"
        self.dataset = json.loads(metadata_path.read_text())
        self.dataset_dir = Path(dataset_dir)
        self.results = []

    async def run(self, languages):

        print("=" * 51)
        print(f"\n{'Lang':<6}{'Sample':<15}{'TTFA(ms)':<12}{'Total(ms)':<12}{'Status'}")
        print("=" * 51)

        for lang in languages:
            for s in self.dataset["languages"][lang]["samples"]:
                sample_id = s["id"]
                text = s["reference_text"]

                ttfa, total, audio_bytes = await self.provider.synthesize(text, lang)

                self.results.append(
                    dict(
                        lang=lang,
                        id=sample_id,
                        ttfa_ms=round(ttfa, 1),
                        total_ms=round(total, 1),
                        audio_bytes=audio_bytes,
                        input_text=text,
                    )
                )
                
                print(f"{lang:<6}{sample_id:<15}{ttfa:<12.1f}{total:<12.1f}OK")

    def save(self, path="results/tts_benchmark.json"):
        utils.save_json(self.results, path)

