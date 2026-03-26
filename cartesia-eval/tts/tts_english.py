import os
import cartesia
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

# Initialize Cartesia client
client = cartesia.Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

# Text to convert to speech
text = "Hello! This is a test of Cartesia text to speech in English."

print("Generating English TTS audio...")

# Generate audio - .generate() returns BinaryAPIResponse
response = client.tts.generate(
    model_id="sonic-3",
    transcript=text,
    voice={
        "mode": "id",
        "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"
    },
    language="en",
    output_format={
        "container": "wav",
        "encoding": "pcm_f32le",
        "sample_rate": 44100
    }
)

# ✅ Correct way - BinaryAPIResponse has write_to_file() method
output_path = "../results/tts_english_output.wav"
response.write_to_file(output_path)

print(f"✅ Done! Audio saved to {output_path}")