import re
from jiwer import wer as jiwer_wer, cer as jiwer_cer

def _normalize(text, lang):
    text = text.lower()
    if lang in ("hi", "bn", "ta", "te"):
        text = re.sub(r'[^\w\s\u0900-\u097f\u0980-\u09ff\u0b80-\u0bff\u0c00-\u0c7f]', '', text)
    else:
        text = re.sub(r'[^\w\s]', '', text)
    return " ".join(text.split())


def calculate_wer(reference, hypothesis, lang):
    reference, hypothesis = _normalize(reference, lang), _normalize(hypothesis, lang)
    return jiwer_wer(reference, hypothesis)

def calculate_cer(reference, hypothesis, lang):
    reference, hypothesis = _normalize(reference, lang), _normalize(hypothesis, lang)
    return jiwer_cer(reference, hypothesis)
