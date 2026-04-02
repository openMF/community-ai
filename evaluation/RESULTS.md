# This file was refined using an AI model (Claude Opus 4.6) under my supervision
# AI-167: Multilingual STT Evaluation Results

**Jira Ticket:** [AI-167 - Evaluate multilingual support for smallest ai](https://mifosforge.jira.com/browse/AI-167)

**Repository:** [aksh08022006/community-ai](https://github.com/aksh08022006/community-ai)

---

## Evaluation Overview

This document tracks findings and results from evaluating multilingual Speech-to-Text (STT) support using whisper.cpp for mobile/edge device inference.

## Objective

Measure performance of whisper-tiny, whisper-base, and whisper-small across 5 languages (English, Hindi, Spanish, French, German) with focus on:
- **Accuracy**: WER (Word Error Rate) / CER (Character Error Rate)
- **Speed**: Latency (inference time)
- **Size**: Model disk footprint and memory usage
- **Optimization**: Edge device constraints

## How to Reproduce

```bash
# Clone repo
git clone https://github.com/aksh08022006/community-ai.git
cd community-ai

# Initialize submodule
cd evaluation
git submodule update --init

# Build whisper.cpp
cd whisper.cpp
cmake -B build
cmake --build build -j --config Release
cd ..

# Run evaluation
python run_multilingual_eval.py
```

See [SETUP.md](./SETUP.md) for detailed instructions.

## Results (Updated as benchmarks run)

### Test Environment
- Date: _[To be filled]_
- Hardware: _[CPU/GPU specs]_
- OS: _[macOS/Linux/Windows]_

### Whisper-Tiny
| Language | WER (%) | CER (%) | Latency (ms) | Notes |
|----------|---------|---------|--------------|-------|
| English  | _TBD_   | _TBD_   | _TBD_        | _     |
| Hindi    | _TBD_   | _TBD_   | _TBD_        | _     |
| Spanish  | _TBD_   | _TBD_   | _TBD_        | _     |
| French   | _TBD_   | _TBD_   | _TBD_        | _     |
| German   | _TBD_   | _TBD_   | _TBD_        | _     |

### Whisper-Base
| Language | WER (%) | CER (%) | Latency (ms) | Notes |
|----------|---------|---------|--------------|-------|
| English  | _TBD_   | _TBD_   | _TBD_        | _     |
| Hindi    | _TBD_   | _TBD_   | _TBD_        | _     |
| Spanish  | _TBD_   | _TBD_   | _TBD_        | _     |
| French   | _TBD_   | _TBD_   | _TBD_        | _     |
| German   | _TBD_   | _TBD_   | _TBD_        | _     |

### Whisper-Small
| Language | WER (%) | CER (%) | Latency (ms) | Notes |
|----------|---------|---------|--------------|-------|
| English  | _TBD_   | _TBD_   | _TBD_        | _     |
| Hindi    | _TBD_   | _TBD_   | _TBD_        | _     |
| Spanish  | _TBD_   | _TBD_   | _TBD_        | _     |
| French   | _TBD_   | _TBD_   | _TBD_        | _     |
| German   | _TBD_   | _TBD_   | _TBD_        | _     |

### Model Size & Memory
| Model      | Disk Size | RAM Usage | Notes |
|-----------|-----------|-----------|-------|
| tiny      | _TBD_     | _TBD_     | _     |
| base      | _TBD_     | _TBD_     | _     |
| small     | _TBD_     | _TBD_     | _     |

## Key Findings

_[To be updated after running benchmarks]_

- Trade-offs observed: accuracy vs latency vs model size
- Best model for mobile: _[TBD]_
- Language-specific insights: _[TBD]_
- Optimization opportunities: _[TBD]_

## Next Steps

- [ ] Run benchmarks on actual mobile device (iOS/Android)
- [ ] Compare quantized vs full-precision models
- [ ] Test on Raspberry Pi for edge inference
- [ ] Document optimization strategies for production deployment
- [ ] AI-174 (Whisper Small variants follow-up)

## References

- whisper.cpp: https://github.com/ggml-org/whisper.cpp
- OpenAI Whisper: https://github.com/openai/whisper
- Common Voice Dataset: https://commonvoice.mozilla.org/
