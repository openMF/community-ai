import speech_recognition as sr
from pydub import AudioSegment
import os
import torch
import librosa
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import logging
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary mapping language codes to pretrained models
LANGUAGE_MODELS = {
    'en-US': 'Harveenchadha/vakyansh-wav2vec2-indian-english-enm-700',
    'hi-IN': 'Harveenchadha/vakyansh-wav2vec2-hindi-him-4200',
    'ta-IN': 'Harveenchadha/vakyansh-wav2vec2-tamil-tam-250',
    'default': 'facebook/wav2vec2-large-xlsr-53'  # Multilingual model as fallback
}

# Cache for loaded models to avoid reloading
_model_cache = {}

def convert_audio_format(audio_path):
    """
    Convert audio to WAV format if needed.
    Returns the path to a WAV file or raises an exception if conversion fails.
    """
    try:
        # Check if file exists and has content
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if os.path.getsize(audio_path) == 0:
            raise ValueError(f"Audio file is empty: {audio_path}")
            
        # If it's already a WAV file, try to validate it
        if audio_path.lower().endswith('.wav'):
            try:
                with sr.AudioFile(audio_path) as source:
                    # This will raise an exception if the file is not a valid WAV
                    sr.Recognizer().record(source)
                return audio_path
            except Exception as e:
                logger.warning(f"Existing WAV file is not valid, will try to convert: {str(e)}")
                # Continue to conversion
        
        # Create a unique filename in the same directory for the converted file
        base_dir = os.path.dirname(audio_path)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        wav_path = os.path.join(base_dir, f"{base_name}_converted_{os.urandom(4).hex()}.wav")
        
        # Try multiple methods to convert the audio
        try:
            # Method 1: Try using pydub with explicit format
            file_ext = os.path.splitext(audio_path)[1].lower().replace('.', '')
            if file_ext:
                try:
                    audio = AudioSegment.from_file(audio_path, format=file_ext)
                    audio.export(wav_path, format='wav')
                    logger.info(f"Successfully converted audio using pydub with format {file_ext}")
                    return wav_path
                except Exception as e1:
                    logger.warning(f"Failed to convert with explicit format {file_ext}: {str(e1)}")
            
            # Method 2: Let pydub guess the format
            try:
                audio = AudioSegment.from_file(audio_path)
                audio.export(wav_path, format='wav')
                logger.info("Successfully converted audio using pydub auto-detection")
                return wav_path
            except Exception as e2:
                logger.warning(f"Failed to convert with pydub auto-detection: {str(e2)}")
            
            # Method 3: Try using ffmpeg directly if available
            try:
                import subprocess
                logger.info("Attempting conversion with direct ffmpeg call")
                result = subprocess.run(
                    ['ffmpeg', '-i', audio_path, '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', wav_path],
                    capture_output=True, text=True, check=False
                )
                if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                    logger.info("Successfully converted audio using ffmpeg")
                    return wav_path
                else:
                    logger.warning(f"FFMPEG conversion failed: {result.stderr}")
            except Exception as e3:
                logger.warning(f"Failed to convert with ffmpeg: {str(e3)}")
            
            # Method 4: Try using librosa
            try:
                y, sr = librosa.load(audio_path, sr=None)
                import soundfile as sf
                sf.write(wav_path, y, sr)
                logger.info("Successfully converted audio using librosa")
                return wav_path
            except Exception as e4:
                logger.warning(f"Failed to convert with librosa: {str(e4)}")
                
            # All methods failed
            raise Exception("All conversion methods failed. Cannot process this audio format.")
            
        except Exception as e:
            # Clean up failed conversions
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass
            raise e
            
    except Exception as e:
        logger.error(f"Error in audio conversion: {str(e)}")
        raise Exception(f"Audio conversion failed: {str(e)}")

def get_model_and_processor(language):
    """Get or load the model and processor for the specified language."""
    model_name = LANGUAGE_MODELS.get(language, LANGUAGE_MODELS['default'])
    
    if model_name == 'default':
        return None, None
        
    if model_name in _model_cache:
        return _model_cache[model_name]
    
    logger.info(f"Loading model {model_name} for language {language}")
    processor = Wav2Vec2Processor.from_pretrained(model_name)
    model = Wav2Vec2ForCTC.from_pretrained(model_name)
    
    # Cache the loaded model
    _model_cache[model_name] = (processor, model)
    return processor, model

def recognize_speech(audio_path, language='en-US'):
    """
    Recognize speech from audio file using appropriate model for the language.
    """
    try:
        wav_path = convert_audio_format(audio_path)
        
        # For English and other well-supported languages, use SpeechRecognition
        if language == 'en-US' or language not in LANGUAGE_MODELS:
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data, language=language)
                    return text
                except sr.UnknownValueError:
                    return "Speech recognition could not understand audio"
                except sr.RequestError:
                    return "Could not request results from speech recognition service"
        
        # For low-resource languages, use specialized models
        else:
            processor, model = get_model_and_processor(language)
            
            # Load and preprocess the audio
            speech_array, sampling_rate = librosa.load(wav_path, sr=16000)
            inputs = processor(speech_array, sampling_rate=16000, return_tensors="pt", padding=True)
            
            with torch.no_grad():
                logits = model(inputs.input_values).logits
            
            # Get predicted ids and convert to text
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = processor.batch_decode(predicted_ids)
            
            return transcription[0]
    
    except Exception as e:
        logger.error(f"Error in speech recognition: {str(e)}")
        return f"Error processing speech: {str(e)}"
    finally:
        # Clean up temporary converted file if it's different from the original
        if 'wav_path' in locals() and wav_path != audio_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except:
                pass
