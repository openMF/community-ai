import os
import cartesia
from dotenv import load_dotenv

load_dotenv()

client = cartesia.Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

text = "¡Hola! Esta es una prueba de texto a voz de Cartesia en español."

print("Generating Spanish TTS audio...")

response = client.tts.generate(
    model_id="sonic-2",
    transcript=text,
    voice={
        "mode": "id",
        "id": "59b37da2-92ba-401a-9e4e-b1d16898d9bc"  # Andrea - Spanish
    },
    language="es",
    output_format={
        "container": "wav",
        "encoding": "pcm_f32le",
        "sample_rate": 44100
    }
)

output_path = "../results/tts_spanish_output.wav"
response.write_to_file(output_path)

print(f"✅ Done! Audio saved to {output_path}")