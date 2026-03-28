import whisper

model = whisper.load_model("medium")

def transcribe(audio_path, lang=None):

    try:
        if lang:
            result = model.transcribe(audio_path, language=lang)
        else:
            result = model.transcribe(audio_path)

        return result["text"].lower().strip()

    except Exception as e:
        print("Whisper error:", e)
        return ""