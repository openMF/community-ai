# PR: AI-172 Foundation - Deepgram Multilingual Evaluation

## What This PR Does

Adds foundation code to evaluate Deepgram's multilingual speech-to-text support:

1. **llms.txt** - Project documentation for Claude/AI tools
2. **SKILL.md** - Defines reusable evaluation skills (/benchmark-speech, /evaluate-language)
3. **providers/deepgram.py** - Deepgram API wrapper for async transcription
4. **metrics/accuracy.py** - WER/CER calculation for accuracy measurement
5. **dataset/ai172_languages.py** - Languages to test (English, Spanish, Hindi, Swahili, French, Portuguese)

**Total: 426 lines across 5 files**

---

## Files

| File | Purpose |
|------|---------|
| llms.txt | Makes project AI-friendly for Claude |
| SKILL.md | Defines AI automation workflows |
| providers/deepgram.py | Deepgram API integration |
| metrics/accuracy.py | WER/CER metrics calculation |
| dataset/ai172_languages.py | Language targets for evaluation |

---

## Testing

```bash
# Test provider loads
from benchmarking_experiments.providers.deepgram import DeepgramSTTProvider

# Test metrics work
from benchmarking_experiments.metrics.accuracy import calculate_wer
calculate_wer("hello world", "hallo world")  # → 0.5

# See languages
from benchmarking_experiments.dataset.ai172_languages import get_languages()
```

---


