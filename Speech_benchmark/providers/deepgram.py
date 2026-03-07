import os
from deepgram import DeepgramClient, PrerecordedOptions

API_KEY = os.getenv("6d360cd097302839b720a11bdc007eacf6a3f783")


deepgram = DeepgramClient(API_KEY)

def transcribe(audio_path):

    try:
        with open(audio_path, "rb") as audio:

            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True
            )

            response = deepgram.listen.prerecorded.v("1").transcribe_file(
                {"buffer": audio},
                options
            )

        text = response["results"]["channels"][0]["alternatives"][0]["transcript"]

        return text

    except Exception as e:
        print("Deepgram error:", e)
        return ""