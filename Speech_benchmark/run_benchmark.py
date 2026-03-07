import os

from providers import whisper
from evaluation.wer import calculate_wer


dataset = [
    {
        "file": "datasets/english_audio/sample1.wav",
        "text": "show my loan balance"
    },
    {
        "file": "datasets/hindi_audio/sample1.wav",
        "text": "mera loan balance batao"
    }
]


providers = {
    "whisper": whisper.transcribe
}


for provider_name, transcribe in providers.items():

    print("\nProvider:", provider_name)

    for sample in dataset:

        predicted = transcribe(sample["file"])

        error = calculate_wer(sample["text"], predicted)

        print("Audio:", sample["file"])
        print("Expected:", sample["text"])
        print("Predicted:", predicted)
        print("WER:", error)
        print("-----")