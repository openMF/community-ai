import asyncio
import time
import os
from dotenv import load_dotenv

# We need to simulate the imports as they exist in the module
from sarvam_tts import generate_speech
from sarvam_stt import transcribe_audio_file

load_dotenv()

TEST_CASES = [
    {
        "language_name": "Hindi",
        "language_code": "hi",
        "text": "आपका स्वागत है! यह एक परीक्षण संदेश है।"
    },
    {
        "language_name": "Bengali",
        "language_code": "bn",
        "text": "স্বাগতম! এটি একটি পরীক্ষামূলক বার্তা।"
    },
    {
        "language_name": "Tamil",
        "language_code": "ta",
        "text": "வரவேற்கிறோம்! இது ஒரு சோதனை செய்தி."
    },
    {
        "language_name": "Punjabi",
        "language_code": "pa",
        "text": "ਜੀ ਆਇਆਂ ਨੂੰ! ਇਹ ਇੱਕ ਟੈਸਟ ਸੁਨੇਹਾ ਹੈ।"
    }
]

async def run_evaluation():
    print("🚀 Starting Sarvam AI Multilingual Evaluation...")
    print("-" * 50)
    
    results = []

    for case in TEST_CASES:
        lang_name = case["language_name"]
        lang_code = case["language_code"]
        source_text = case["text"]
        output_file = f"eval_output_{lang_code}.wav"
        
        print(f"\n[{lang_name} ({lang_code})]")
        print(f"Target Text: {source_text}")
        
        # 1. Test TTS
        tts_start = time.time()
        print(f"Synthesizing speech via Bulbul v3...")
        # Awaiting because generate_speech is an async function
        audio_path = await generate_speech(text=source_text, language=lang_code, output_file=output_file)
        tts_end = time.time()
        tts_latency = round(tts_end - tts_start, 2)
        
        if not audio_path or not os.path.exists(output_file):
            print("❌ TTS Failed.")
            continue
            
        print(f"✅ TTS Success ({tts_latency}s)")
        
        # 2. Test STT
        stt_start = time.time()
        print(f"Transcribing {output_file} via Saaras v3...")
        transcription = transcribe_audio_file(file_path=output_file, language=lang_code)
        stt_end = time.time()
        stt_latency = round(stt_end - stt_start, 2)
        
        if not transcription:
            print("❌ STT Failed.")
            continue
            
        print(f"✅ STT Success ({stt_latency}s)")
        print(f"Result: {transcription[:100]}...") # Print first 100 chars
        
        # Cleanup
        if os.path.exists(output_file):
            os.remove(output_file)
            
        # Record successful metric
        results.append({
            "Language": lang_name,
            "TTS_Latency_Seconds": tts_latency,
            "STT_Latency_Seconds": stt_latency,
            "Success": True
        })
        
    print("\n" + "="*50)
    print("📊 Evaluation Summary:")
    print(f"Total Languages Tested: {len(TEST_CASES)}")
    print(f"Successful Pipelines: {len(results)}")
    
    for r in results:
        print(f"- {r['Language']}: TTS={r['TTS_Latency_Seconds']}s, STT={r['STT_Latency_Seconds']}s")

if __name__ == "__main__":
    if not os.getenv("SARVAM_API_KEY"):
        print("ERROR: SARVAM_API_KEY environment variable not found.")
        exit(1)
        
    asyncio.run(run_evaluation())
