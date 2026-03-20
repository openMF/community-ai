import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import time
import os

_processor = None
_model = None

def get_hf_model(model_name="openai/whisper-small"):
    global _processor, _model
    if _model is None or _model.config._name_or_path != model_name:
        print(f"Loading Hugging Face model: {model_name}...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _processor = WhisperProcessor.from_pretrained(model_name)
        _model = WhisperForConditionalGeneration.from_pretrained(model_name).to(device)
    return _processor, _model

def transcribe_hf(audio_array, sampling_rate=16000, model_name="openai/whisper-small", language="hi", task="transcribe"):
    """
    Transcribe audio using Hugging Face Whisper model.
    """
    processor, model = get_hf_model(model_name)
    device = model.device
    
    # Preprocess audio
    input_features = processor(audio_array, sampling_rate=sampling_rate, return_tensors="pt").input_features.to(device)
    
    # Logic to handle forced_decoder_ids safely
    # If it's English-only or certain distilled variants, they don't support forced_decoder_ids
    generate_kwargs = {}
    if ".en" not in model_name and "distil" not in model_name.lower():
        try:
            forced_ids = processor.get_decoder_prompt_ids(language=language, task=task)
            generate_kwargs["forced_decoder_ids"] = forced_ids
        except Exception:
            pass
    
    # Standard inference cycle for the Whisper model
    start_time = time.time()
    try:
        with torch.no_grad():
            predicted_ids = model.generate(input_features, **generate_kwargs)
    except Exception as e:
        print(f"Warning: Specialist model {model_name} require native defaults. Retrying without kwargs. Error: {e}")
        with torch.no_grad():
            predicted_ids = model.generate(input_features)
    latency = time.time() - start_time
    
    # Decode
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    
    return transcription, latency
