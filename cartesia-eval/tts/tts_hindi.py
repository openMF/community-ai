import os
import cartesia
from dotenv import load_dotenv

load_dotenv()

client = cartesia.Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

text = "नमस्ते! यह कार्टेशिया टेक्स्ट टू स्पीच का हिंदी परीक्षण है।"

print("Generating Hindi TTS audio...")

response = client.tts.generate(
    model_id="sonic-2",
    transcript=text,
    voice={
        "mode": "id",
        "id": "bdab08ad-4137-4548-b9db-6142854c7525"  # Imran - Hindi Film Actor
    },
    language="hi",
    output_format={
        "container": "wav",
        "encoding": "pcm_f32le",
        "sample_rate": 44100
    }
)

output_path = "../results/tts_hindi_output.wav"
response.write_to_file(output_path)

print(f"✅ Done! Audio saved to {output_path}")