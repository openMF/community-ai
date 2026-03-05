# 📊 Sarvam AI (Saaras & Bulbul) Multilingual Evaluation Results

This document contains the empirical findings from our end-to-end evaluation of the Sarvam AI STT & TTS pipelines integrated into the Voice Banking application. The primary goal of Jira Ticket [AI-167] was to evaluate the suitability of these models for edge device deployments (iOS, Android) with Indic language workloads.

## Test Environment ⚙️
- **Platform**: Python 3.13 (macOS)
- **APIs Evaluated**: `bulbul:v3` (Text-to-Speech), `saaras:v3` (Speech-to-Text)
- **Methodology**: 
  1. Synthesize localized text into a `.wav` file (measuring network/inference TTS latency).
  2. Feed the generated `.wav` file back into the STT engine for transcription (measuring STT latency).
  3. Validate success payload and stability.

## Performance Matrix ⏱️

The results below reflect the end-to-end network operation time (inference + download/upload).

| Language | Locale Code | Target Text | TTS Latency (Bulbul v3) | STT Latency (Saaras v3) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hindi** | `hi-IN` | आपका स्वागत है! यह एक परीक्षण संदेश है। | 0.81s | 0.96s | ✅ Success |
| **Bengali** | `bn-IN` | স্বাগতম! এটি একটি পরীক্ষামূলক বার্তা। | 0.90s | 0.70s | ✅ Success |
| **Tamil** | `ta-IN` | வரவேற்கிறோம்! இது ஒரு சோதனை செய்தி. | 0.88s | 0.73s | ✅ Success |
| **Punjabi** | `pa-IN` | ਜੀ ਆਇਆਂ ਨੂੰ! ਇਹ ਇੱਕ ਟੈਸਟ ਸੁਨੇਹਾ ਹੈ। | 0.86s | 0.58s | ✅ Success |

## Key Findings 🔍

1. **Sub-second Inference:** Across 4 highly distinct Indian languages, Sarvam consistently returned audio synthesis and transcriptions in **under 1 second**. This is a dramatic improvement over local CPU/RAM-bound execution of Hugging Face/Whisper architectures on constrained devices.
2. **Grammar & Phonetics:** Bulbul v3 managed localized syntax inherently (without needing English-based transliteration workarounds), creating natural-sounding prosody for Tamil and Bengali.
3. **Hardware Unblocking:** By replacing the on-device PyTorch model loading with this API strategy, mobile devices and constrained edge machines (e.g., Raspberry Pi) are entirely unburdened from VRAM requirements.

## Reproduction
To recreate these metrics locally, navigate to this submodule and run the standalone wrapper:

```bash
python run_multilingual_eval.py
```
