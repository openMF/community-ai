# Cartesia Multilingual Evaluation (AI-168)

Evaluation of Cartesia's TTS (Text-to-Speech) and STT (Speech-to-Text) 
capabilities for multilingual support across English, Hindi, and Spanish.

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Create a `.env` file in this folder:
```
CARTESIA_API_KEY=your_api_key_here
```

## Project Structure
```
cartesia-eval/
├── tts/
│   ├── tts_english.py       # English TTS
│   ├── tts_hindi.py         # Hindi TTS
│   └── tts_spanish.py       # Spanish TTS
├── stt/
│   ├── stt_english.py       # English STT
│   ├── stt_hindi.py         # Hindi STT
│   └── stt_spanish.py       # Spanish STT
├── results/                 # Generated audio + transcription outputs
├── .env                     # API key (not committed to Git)
├── requirements.txt
└── README.md
```

## Models Used
- **TTS:** `sonic-2`
- **STT:** `ink-whisper`

## Languages Evaluated
| Language | TTS | STT |
|----------|-----|-----|
| English  | ✅  | ✅  |
| Hindi    | ✅  | ✅  |
| Spanish  | ✅  | ✅  |

## Results
- All 3 languages produce clear, natural-sounding TTS audio
- STT accurately transcribes audio with correct language detection
- Duration per transcription: ~3-4 seconds