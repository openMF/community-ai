import json
from pathlib import Path
import utils

async def run_sts(provider, langs, dataset_dir):
    evaluator = STSEvaluator(provider, dataset_dir)
    await evaluator.run(langs)
    evaluator.save()

class STSEvaluator:
    def __init__(self, provider, dataset_dir="mifos_audio_benchmarking"):
        self.provider = provider
        metadata_path = Path(dataset_dir) / "metadata.json"
        self.dataset = json.loads(metadata_path.read_text())
        self.dataset_dir = Path(dataset_dir)
        self.results = []

    async def run(self, languages):
        print("=" * 42)
        print(f"\n{'Lang':<6}{'Sample':<15}{'TTFA(ms)':<15}{'Status'}")
        print("=" * 42)
        for lang in languages:
            for s in self.dataset["languages"][lang]["samples"]:
                sid = s["id"]
                audio = str(self.dataset_dir / s["audio_path"])
                ttfa = await self.provider.measure_ttfa(audio, lang)
                self.results.append(
                    dict(
                        lang=lang,
                        id=sid,
                        ttfa_ms=round(ttfa, 1)
                    )
                )
                
                print(f"{lang:<6}{sid:<15}{ttfa:<15.1f}OK")
            

    def save(self, path="results/sts_benchmark.json"):
        utils.save_json(self.results, path)
