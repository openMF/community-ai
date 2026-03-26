import os
import cartesia
from dotenv import load_dotenv

load_dotenv()

client = cartesia.Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

audio_path = "../results/tts_hindi_output.wav"

print("Transcribing Hindi audio...")

with open(audio_path, "rb") as audio_file:
    response = client.stt.transcribe(
        file=("tts_hindi_output.wav", audio_file, "audio/wav"),
        model="ink-whisper",
        language="hi",
    )

print(f"✅ Transcription: {response.text}")
print(f"   Language detected: {response.language}")
print(f"   Duration: {response.duration}s")

with open("../results/stt_hindi_result.txt", "w", encoding="utf-8") as f:
    f.write(f"Transcription: {response.text}\n")
    f.write(f"Language: {response.language}\n")
    f.write(f"Duration: {response.duration}s\n")

print("✅ Result saved to ../results/stt_hindi_result.txt")