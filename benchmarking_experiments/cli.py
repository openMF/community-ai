import os

from providers import whisper
from results.wer import calculate_wer


providers = {
    "whisper": whisper.transcribe
}

datasets = {
    "english": "dataset/audio/english_audio",
    "hindi": "dataset/audio/hindi_audio",
    "spanish": "dataset/audio/spanish_audio",
    "french": "dataset/audio/french_audio",
    "portuguese": "dataset/audio/portuguese_audio"
}


for provider_name, transcribe in providers.items():

    print("\nProvider:", provider_name)

    for lang, folder in datasets.items():

        print("\nLanguage:", lang)

        for file in os.listdir(folder):

            if file.endswith(".wav"):

                audio_path = os.path.join(folder, file)

                # corresponding transcript
                txt_file = file.replace(".wav", ".txt")
                txt_path = os.path.join(folder, txt_file)

                if not os.path.exists(txt_path):
                    print("Transcript missing for:", file)
                    continue

                with open(txt_path, "r", encoding="utf-8") as f:
                    expected_text = f.read().strip()

                predicted = transcribe(audio_path)

                error = calculate_wer(expected_text, predicted)

                print("Audio:", file)
                print("Expected:", expected_text)
                print("Predicted:", predicted)
                print("WER:", error)
                print("-----")