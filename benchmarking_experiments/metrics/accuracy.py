"""
Speech Accuracy Metrics - WER & CER calculation

Required for AI-172: Evaluate Deepgram multilingual accuracy
"""

import re
from typing import Tuple


def normalize_text(text: str) -> str:
    """Normalize text for fair comparison (lowercase, remove extra spaces)"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Keep words and spaces only
    return ' '.join(text.split())  # Remove extra whitespace


def edit_distance(ref: list, hyp: list) -> Tuple[int, int, int, int]:
    """
    Calculate edit distance (Wagner-Fischer algorithm)
    Returns: (matches, insertions, deletions, substitutions)
    """
    m, n = len(ref), len(hyp)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    
    # Backtrack to count operations
    matches = insertions = deletions = substitutions = 0
    i, j = m, n
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hyp[j - 1]:
            matches += 1
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            substitutions += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            deletions += 1
            i -= 1
        else:
            insertions += 1
            j -= 1
    
    return matches, insertions, deletions, substitutions


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Word Error Rate = (S + D + I) / N
    where S=subs, D=deletions, I=insertions, N=ref_words
    """
    ref_words = normalize_text(reference).split()
    hyp_words = normalize_text(hypothesis).split()
    
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    
    _, insertions, deletions, substitutions = edit_distance(ref_words, hyp_words)
    wer = (substitutions + deletions + insertions) / len(ref_words)
    return min(wer, 1.0)


def calculate_cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate (same formula but for characters, excluding whitespace)"""
    ref_chars = re.sub(r'\s+', '', normalize_text(reference))
    hyp_chars = re.sub(r'\s+', '', normalize_text(hypothesis))
    
    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0
    
    _, insertions, deletions, substitutions = edit_distance(list(ref_chars), list(hyp_chars))
    cer = (substitutions + deletions + insertions) / len(ref_chars)
    return min(cer, 1.0)


def evaluate_sample(reference: str, hypothesis: str) -> dict:
    """Evaluate single transcription"""
    wer = calculate_wer(reference, hypothesis)
    cer = calculate_cer(reference, hypothesis)
    mos = 5 - (wer * 4)  # Simple MOS estimate
    
    return {
        "wer": round(wer, 4),
        "cer": round(cer, 4),
        "mos": round(max(1.0, min(5.0, mos)), 2),
    }
