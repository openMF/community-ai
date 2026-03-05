import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

# Ensure we can import from services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services import sarvam_stt
from services import sarvam_tts

async def main():
    print("--- Testing Sarvam AI Voice Pipeline ---")
    
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        print("❌ Error: SARVAM_API_KEY environment variable is not set.")
        print("Run this script as: SARVAM_API_KEY='your_key' python test_audio_pipeline.py")
        return

    # You need a sample .wav file to test STT
    test_audio_input = "test_input.wav" 
    test_audio_output = "test_output.wav"
    
    print("\n[1] Testing Text-to-Speech (TTS)")
    test_text = "आपका स्वागत है! यह एक परीक्षण संदेश है।" # Hindi: Welcome! This is a test message.
    print(f"Text to synthesize: {test_text}")
    print("Generating speech in Hindi (hi)...")
    
    # We use "hi" to mimic what the frontend sends, sarvam_tts maps "hi" -> "hi-IN"
    output_path = await sarvam_tts.generate_speech(text=test_text, language="hi", output_file=test_audio_output)
    
    if output_path and os.path.exists(output_path):
        print(f"✅ TTS Success! Audio saved to {output_path}")
        
        print("\n[2] Testing Speech-to-Text (STT)")
        print(f"We will now transcribe the audio we just generated ({output_path})...")
        
        # We pass the generated audio back into our STT pipeline
        transcription = sarvam_stt.transcribe_audio_file(output_path, language="hi", mode="transcribe")
        
        if transcription:
            print(f"✅ STT Success! Transcribed Text: {transcription}")
        else:
            print("❌ STT Failed to generate transcription.")
    else:
        print("❌ TTS Failed to generate audio.")

if __name__ == "__main__":
    asyncio.run(main())
