from jiwer import wer, cer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

def calculate_wer(reference, hypothesis):
    """
    Calculate Word Error Rate (WER).
    """
    if not hypothesis:
        return 1.0 # 100% error if no prediction
    return wer(reference, hypothesis)

def calculate_cer(reference, hypothesis):
    """
    Calculate Character Error Rate (CER).
    """
    if not hypothesis:
        return 1.0
    return cer(reference, hypothesis)

def calculate_bleu(reference, hypothesis):
    """
    Calculate BLEU Score (Bilingual Evaluation Understudy).
    Returns a score from 0.0 to 1.0.
    """
    if not hypothesis:
        return 0.0
    
    # BLEU requires tokenized lists
    ref_tokens = [reference.split()]
    hyp_tokens = hypothesis.split()
    
    # Using smoothing to handle short sentences / no n-gram overlap
    chencherry = SmoothingFunction()
    try:
        score = sentence_bleu(ref_tokens, hyp_tokens, smoothing_function=chencherry.method1)
        return score
    except Exception:
        return 0.0
