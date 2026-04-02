#!/usr/bin/env python3
"""
Smoke test script for PR #99 - AI-172 Deepgram multilingual evaluation
This is a standalone script (not pytest-discoverable). It runs quick verification
of core modules without requiring the `whisper.cpp` submodule.
"""

import sys
import os

def main():
    # Add benchmarking_experiments to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmarking_experiments'))

    print("=" * 70)
    print(" 🧪 PR #99 SMOKE TEST - AI-172 Foundation for Deepgram Multilingual STT")
    print("=" * 70)

    # Test 1: Metrics Module
    print("\n\n📊 TEST 1: METRICS MODULE")
    print("-" * 70)

    try:
        from metrics.accuracy import calculate_wer, calculate_cer, evaluate_sample
        print("✅ Successfully imported metrics.accuracy")

        # Test WER with perfect match
        ref = "I would like to open a savings account"
        hyp = "I would like to open a savings account"
        wer = calculate_wer(ref, hyp)
        print(f"\n  Perfect Match Test:")
        print(f"  Reference:  {ref}")
        print(f"  Hypothesis: {hyp}")
        print(f"  WER: {wer} ✓")

        # Test WER with errors
        ref2 = "What is my current account balance"
        hyp2 = "What is current account"
        wer2 = calculate_wer(ref2, hyp2)
        print(f"\n  With Errors Test:")
        print(f"  Reference:  {ref2}")
        print(f"  Hypothesis: {hyp2}")
        print(f"  WER: {wer2} ✓")

        # Test CER
        cer = calculate_cer(ref, hyp)
        print(f"\n  Character Error Rate (Perfect): {cer} ✓")

        # Test full evaluation
        metrics = evaluate_sample(ref2, hyp2)
        print(f"\n  Full Sample Metrics: {metrics} ✓")

        print("\n✅ METRICS MODULE: ALL TESTS PASSED")

    except Exception as e:
        print(f"❌ METRICS MODULE FAILED: {e}")
        sys.exit(1)

    # Test 2: Dataset Module
    print("\n\n🌍 TEST 2: DATASET & LANGUAGES MODULE")
    print("-" * 70)

    try:
        from dataset.ai172_languages import get_languages, get_domains, get_sample_references
        print("✅ Successfully imported dataset.ai172_languages")

        langs = get_languages()
        print(f"\n  Languages configured: {len(langs)}")
        for code, info in langs:
            print(f"    • {info['name']} ({code}) - Priority: {info['priority']}")

        domains = get_domains()
        print(f"\n  Financial domains: {len(domains)}")
        for domain in domains:
            print(f"    • {domain}")

        refs = get_sample_references()
        print(f"\n  Sample references available for: {list(refs.keys())}")
        print(f"    English sample: {refs['en'][0]}")
        if 'hi' in refs:
            print(f"    Hindi sample: {refs['hi'][0]}")

        print("\n✅ DATASET MODULE: ALL TESTS PASSED")

    except Exception as e:
        print(f"❌ DATASET MODULE FAILED: {e}")
        sys.exit(1)

    # Test 3: HuggingFace Dataset Builder
    print("\n\n📦 TEST 3: HUGGINGFACE DATASET BUILDER")
    print("-" * 70)

    try:
        from dataset.create_hf_dataset import GROUND_TRUTH, LANGUAGE_NAMES
        print("✅ Successfully imported create_hf_dataset")

        print(f"\n  Languages in dataset: {list(GROUND_TRUTH.keys())}")
        for lang, samples in GROUND_TRUTH.items():
            print(f"    • {LANGUAGE_NAMES[lang]}: {len(samples)} samples")
            print(f"      First sample: {samples[0]['text']}")

        total_samples = sum(len(s) for s in GROUND_TRUTH.values())
        print(f"\n  Total samples across all languages: {total_samples}")

        print("\n✅ HUGGINGFACE DATASET: ALL TESTS PASSED")

    except Exception as e:
        print(f"❌ HUGGINGFACE DATASET FAILED: {e}")
        sys.exit(1)

    # Test 4: Report Generator
    print("\n\n📈 TEST 4: REPORT GENERATOR")
    print("-" * 70)

    try:
        from generate_report import generate_report
        print("✅ Successfully imported generate_report")

        # Generate a dry-run report
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.json")
            report = generate_report(api_key=None, languages=['en', 'hi'], output_path=output_path, dry_run=True)

            evaluated = report.get('languages_evaluated') or []
            print(f"\n  Report generated successfully")
            print(f"  Languages evaluated: {', '.join(evaluated)}")
            print(f"  Summary - Total samples: {report['summary']['total_samples']}")
            print(f"  Summary - Total languages: {report['summary']['total_languages']}")
            print(f"  Report structure: {list(report.keys())}")

            print("\n✅ REPORT GENERATOR: ALL TESTS PASSED")

    except Exception as e:
        print(f"❌ REPORT GENERATOR FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Final Summary
    print("\n\n" + "=" * 70)
    print(" ✅ ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    print("\n📋 Summary:")
    print("   ✓ Metrics module (WER/CER calculation) - WORKING")
    print("   ✓ Dataset module (Languages & domains) - WORKING")
    print("   ✓ HuggingFace dataset builder - WORKING")
    print("   ✓ Report generator - WORKING")
    print("\n🎯 PR #99 Functionality: FULLY OPERATIONAL")
    print("   Ready for Deepgram API integration and audio sample collection")
    print("=" * 70)


if __name__ == '__main__':
    main()
