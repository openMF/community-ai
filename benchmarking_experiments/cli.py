from datasets import load_dataset
import soundfile as sf
from providers import whisper


dataset = load_dataset("keshavagrawal02/multilingual", streaming=True)

for sample in dataset["train"]:

    audio = sample["audio"]

    # HF gives dict
    array = audio["array"]
    sr = audio["sampling_rate"]

    sf.write("temp.wav", array, sr)

    predicted = whisper.transcribe("temp.wav")
    

    print("Predicted:", predicted)

    print("-----")