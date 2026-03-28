import re
import torch
from typing import List
from sentence_transformers import SentenceTransformer, util

# Keep model loading lazy to avoid startup delay if not used
MODEL = None

def get_model():
    global MODEL
    if MODEL is None:
        MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return MODEL

def normalize_text(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return " ".join(text.split())

def _levenshtein(a: list, b: list) -> int:
    la, lb = len(a), len(b)
    if la == 0: return lb
    if lb == 0: return la
    
    dp = list(range(lb + 1))
    for i in range(1, la + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, lb + 1):
            temp = dp[j]
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[j] = min(dp[j] + 1, dp[j-1] + 1, prev + cost)
            prev = temp
    return dp[lb]

def calculate_wer(ref: str, hyp: str) -> float:
    ref_tokens = normalize_text(ref).split()
    hyp_tokens = normalize_text(hyp).split()
    if not ref_tokens: return 1.0 if hyp_tokens else 0.0
    return _levenshtein(ref_tokens, hyp_tokens) / len(ref_tokens)

def calculate_cer(ref: str, hyp: str) -> float:
    ref_chars = list(normalize_text(ref).replace(" ", ""))
    hyp_chars = list(normalize_text(hyp).replace(" ", ""))
    if not ref_chars: return 1.0 if hyp_chars else 0.0
    return _levenshtein(ref_chars, hyp_chars) / len(ref_chars)

def calculate_jaro_winkler(s1: str, s2: str) -> float:
    def jaro(s1, s2):
        s1_len, s2_len = len(s1), len(s2)
        if s1_len == 0: return 1.0 if s2_len == 0 else 0.0
        
        match_bound = max(0, max(s1_len, s2_len) // 2 - 1)
        s1_m, s2_m = [False]*s1_len, [False]*s2_len
        matches = 0
        
        for i in range(s1_len):
            start = max(0, i - match_bound)
            end = min(i + match_bound + 1, s2_len)
            for j in range(start, end):
                if not s2_m[j] and s1[i] == s2[j]:
                    s1_m[i] = s2_m[j] = True
                    matches += 1
                    break
        
        if matches == 0: return 0.0
        
        t, k = 0, 0
        for i in range(s1_len):
            if s1_m[i]:
                while not s2_m[k]: k += 1
                if s1[i] != s2[k]: t += 1
                k += 1
        return (matches/s1_len + matches/s2_len + (matches - t//2)/matches) / 3

    j = jaro(s1, s2)
    l = 0
    for i in range(min(4, len(s1), len(s2))):
        if s1[i] == s2[i]: l += 1
        else: break
    return j + (l * 0.1 * (1 - j))

def calculate_semantic_similarity(ref: str, hyp: str) -> float:
    if not ref or not hyp: return 0.0
    model = get_model()
    e1 = model.encode(ref, convert_to_tensor=True)
    e2 = model.encode(hyp, convert_to_tensor=True)
    return float(util.cos_sim(e1, e2))

def calculate_entity_accuracy(hyp: str, expected: List[str]) -> float:
    if not expected: return 1.0
    if not hyp: return 0.0
    
    h_norm = normalize_text(hyp)
    found = sum(1 for e in expected if normalize_text(e) in h_norm)
    return found / len(expected)
