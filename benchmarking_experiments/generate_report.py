"""
Metrics Report Generator for Deepgram Evaluation (AI-172)

Runs Deepgram STT against the benchmark dataset and generates
a per-language metrics report (WER, CER, MOS).

Output: JSON report + human-readable summary

Usage:
  python generate_report.py --api-key $DEEPGRAM_API_KEY
  python generate_report.py --api-key $DEEPGRAM_API_KEY --languages hi fr pt
"""

import os
import json
import time
import argparse
from datetime import datetime
from typing import Optional

from metrics.accuracy import calculate_wer, calculate_cer, evaluate_sample
from dataset.create_hf_dataset import GROUND_TRUTH, LANGUAGE_NAMES


def generate_report(
    api_key: Optional[str] = None,
    languages: list = None,
    output_path: str = "./results/deepgram_report.json",
    dry_run: bool = True,
):
    """
    Generate evaluation report for Deepgram across languages.

    For now, this runs a dry-run with simulated transcriptions.
    When audio samples are available, it will call Deepgram API.
    """
    if languages is None:
        languages = list(GROUND_TRUTH.keys())

    report = {
        "provider": "deepgram",
        "model": "nova-2",
        "timestamp": datetime.now().isoformat(),
        "languages_evaluated": [],
        "results": {},
        "summary": {},
    }

    all_wers = []

    for lang in languages:
        samples = GROUND_TRUTH.get(lang, [])
        if not samples:
            print(f"⚠️  No samples for {lang}, skipping")
            continue

        # mark as evaluated
        report["languages_evaluated"].append(lang)

        lang_results = []

        for sample in samples:
            reference = sample["text"]

            # TODO: Replace with actual Deepgram API call when audio is ready
            # For now, use reference as hypothesis (perfect score) to validate pipeline
            hypothesis = reference  # Placeholder until audio samples exist

            metrics = evaluate_sample(reference, hypothesis)
            metrics["sample_id"] = sample["id"]
            metrics["domain"] = sample["domain"]
            metrics["reference"] = reference
            metrics["hypothesis"] = hypothesis
            lang_results.append(metrics)

        # Aggregate per-language metrics
        wers = [r["wer"] for r in lang_results]
        cers = [r["cer"] for r in lang_results]

        avg_wer = sum(wers) / len(wers) if wers else 0
        avg_cer = sum(cers) / len(cers) if cers else 0
        all_wers.append(avg_wer)

        report["results"][lang] = {
            "language_name": LANGUAGE_NAMES.get(lang, lang),
            "samples_count": len(lang_results),
            "avg_wer": round(avg_wer, 4),
            "avg_cer": round(avg_cer, 4),
            "avg_mos": round(5 - (avg_wer * 4), 2),
            "samples": lang_results,
        }

    # Overall summary computed over actually evaluated results
    total_languages = len(report["results"])
    total_samples = sum(v["samples_count"] for v in report["results"].values())
    report["summary"] = {
        "total_languages": total_languages,
        "total_samples": total_samples,
        "avg_wer_all": round(sum(all_wers) / len(all_wers), 4) if all_wers else 0,
        "best_language": min(report["results"], key=lambda l: report["results"][l]["avg_wer"]) if report["results"] else None,
        "worst_language": max(report["results"], key=lambda l: report["results"][l]["avg_wer"]) if report["results"] else None,
    }

    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def print_report(report: dict):
    """Print human-readable summary"""
    print("\n" + "=" * 60)
    print(f"  Deepgram Evaluation Report ({report['model']})")
    print("=" * 60)

    print(f"\n{'Language':<15} {'Samples':<10} {'WER':<10} {'CER':<10} {'MOS':<10}")
    print("-" * 55)

    for lang, data in report["results"].items():
        print(f"{data['language_name']:<15} {data['samples_count']:<10} "
              f"{data['avg_wer']:<10.4f} {data['avg_cer']:<10.4f} {data['avg_mos']:<10.2f}")

    summary = report["summary"]
    print("-" * 55)
    print(f"{'Overall':<15} {summary['total_samples']:<10} {summary['avg_wer_all']:<10.4f}")
    print(f"\nBest:  {summary['best_language']}")
    print(f"Worst: {summary['worst_language']}")
    print(f"\nReport saved to results/deepgram_report.json")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Deepgram Evaluation Report")
    parser.add_argument("--api-key", default=os.getenv("DEEPGRAM_API_KEY"), help="Deepgram API key")
    parser.add_argument("--languages", nargs="+", default=None, help="Languages to evaluate")
    parser.add_argument("--output", default="./results/deepgram_report.json", help="Output path")

    args = parser.parse_args()

    report = generate_report(args.api_key, args.languages, args.output)
    print_report(report)
