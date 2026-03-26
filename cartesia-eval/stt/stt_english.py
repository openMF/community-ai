import os
import cartesia
from dotenv import load_dotenv

load_dotenv()

client = cartesia.Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

# Use the English TTS output we already generated as input
audio_path = "../results/tts_english_output.wav"

print("Transcribing English audio...")

with open(audio_path, "rb") as audio_file:
    response = client.stt.transcribe(
        file=("tts_english_output.wav", audio_file, "audio/wav"),
        model="ink-whisper",
        language="en",
    )

print(f"✅ Transcription: {response.text}")
print(f"   Language detected: {response.language}")
print(f"   Duration: {response.duration}s")

# Save result to results folder
with open("../results/stt_english_result.txt", "w") as f:
    f.write(f"Transcription: {response.text}\n")
    f.write(f"Language: {response.language}\n")
    f.write(f"Duration: {response.duration}s\n")

print("✅ Result saved to ../results/stt_english_result.txt")