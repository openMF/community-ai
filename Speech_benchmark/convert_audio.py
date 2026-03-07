from pydub import AudioSegment

# English audio
audio = AudioSegment.from_mp3("datasets/english_audio/recording_english.mp3")
audio.export("datasets/english_audio/sample1.wav", format="wav")

# Hindi audio
audio = AudioSegment.from_mp3("datasets/hindi_audio/recording_hindi.mp3")
audio.export("datasets/hindi_audio/sample1.wav", format="wav")

print("Conversion completed")