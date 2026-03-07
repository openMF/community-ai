import whisper

model = whisper.load_model("medium")

def transcribe(audio_path):

    try:
        result = model.transcribe(audio_path, language="hi", task="transcribe")
        return result["text"]

    except Exception as e:
        print("Whisper error:", e)
        return ""