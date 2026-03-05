# Sarvam AI Integration: Voice-Driven Banking Findings

This submodule contains the extracted codebase, results, and findings from our evaluation and implementation of **Sarvam AI's** multilingual audio APIs (Saaras v3 and Bulbul v3) into the `Voice-Driven_banking-Lam` project.

As part of the evaluation, we extracted these modules from the core FastApi backend to keep the parent repository exactly as it was, while preserving our functional proof-of-concept here for demonstration and future integration.

## 🎯 Goal
The core objective was to replace the backend's heavy local machine learning components—specifically Hugging Face Whisper (Speech-to-Text) and MMS (Text-to-Speech)—with Sarvam AI's optimized cloud APIs to improve performance, latency, and naturalness for Indic languages.

## 🛠️ The Extracted Modules

### 1. `sarvam_stt.py`
This module handles inbound audio bytes. Using the `sarvamai` Python SDK, it bypasses the heavy local memory load of Whisper by routing the audio file directly to the **Saaras v3** endpoint. It utilizes auto-language detection for optimal transcription.

### 2. `sarvam_tts.py`
This module handles Voice synthesis from LLM-generated text. It routes requests to the **Bulbul v3** model, converting standard ISO language codes into the localized format Sarvam expects (`hi-IN`, `ta-IN`, etc.). During integration, we configured the official `tanya` speaker profile for enhanced naturalness.

### 3. `test_audio_pipeline.py`
A standalone, fully-functional terminal script that proves the end-to-end integration works without needing to spin up the entire FastAPI and Firebase environment. 

## 🧪 Findings and Results 

1. **Resolution of OOM Errors**: The parent Voice-Driven Banking application initializes heavy `torchaudio` and `transformers` wrappers around Whisper. By offloading these models to Sarvam APIs, the backend initialized instantly and avoided memory consumption crashes entirely.
2. **Superior Indic Language Performance**: During testing, the `Bulbul v3` Text-to-Speech pipeline generated flawless localized Hindi audio (`"आपका स्वागत है! यह एक परीक्षण संदेश है।"`) with correct pitch and grammar, avoiding the robotic artifacts commonly found in generic multi-language models.
3. **Integration Speed**: The transcription loop from the generated output back into the **Saaras v3** STT pipeline processed rapidly with a `language_probability` score of 0.998, returning the exact input script.

## 🚀 How to Run the Demonstration

You can run our extracted audio verification pipeline right from your terminal.

1. Create a `.env` file inside **this folder** (`Sarvam_Integration/VoiceBanking_Results/`) and add your key:
```env
SARVAM_API_KEY=your_key_here
```
2. Make sure you are using a Python virtual environment loaded with the SDK.
```bash
pip install sarvamai python-dotenv
```
3. Run the pipeline logic:
```bash
python test_audio_pipeline.py
```

The script will synthesize a Hindi phrase, download the `.wav` file locally, and immediately push the `.wav` file back to the Sarvam STT parser to decode the same text.
