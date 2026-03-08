import asyncio
import time
import os
import re
from dotenv import load_dotenv
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer, util
import torch

# We need to simulate the imports as they exist in the module
from sarvam_tts import generate_speech
from sarvam_stt import transcribe_audio_file

load_dotenv()

# Initialize Multilingual Semantic Model
print("Loading Multilingual Semantic Model (paraphrase-multilingual-MiniLM-L12-v2)...")
MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

TEST_CASES = [
    {
        "language_name": "Hindi",
        "language_code": "hi",
        "text": "मेरे लोन का बैलेंस क्या है?",
        "expected_entities": ["लोन", "बैलेंस"]
    },
    {
        "language_name": "Bengali",
        "language_code": "bn",
        "text": "অর্পিতের অ্যাকাউন্টে পাঁচশ টাকা পাঠাও",
        "expected_entities": ["অর্পিতের", "পাঁচশ", "টাকা"]
    },
    {
        "language_name": "Tamil",
        "language_code": "ta",
        "text": "எனது கடன் இருப்பைச் சரிபார்க்கவும்",
        "expected_entities": ["கடன்", "இருப்பை"]
    },
    {
        "language_name": "Marathi",
        "language_code": "mr",
        "text": "माझ्या खात्यातून दोनशे रुपये वजा करा",
        "expected_entities": ["दोनशे", "रुपये", "खात्यातून"]
    },
    {
        "language_name": "Kannada",
        "language_code": "kn",
        "text": "ನನ್ನ ಸಾಲದ ವಿವರಗಳನ್ನು ತೋರಿಸಿ",
        "expected_entities": ["ಸಾಲದ", "ವಿವರಗಳನ್ನು"]
    }
]

def _levenshtein(a, b):
    """Compute Levenshtein distance between sequences a and b."""
    la, lb = len(a), len(b)
    if la == 0: return lb
    if lb == 0: return la
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1): dp[i][0] = i
    for j in range(lb + 1): dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[la][lb]

def wer(ref: str, hyp: str) -> float:
    ref_tokens = ref.strip().lower().split()
    hyp_tokens = hyp.strip().lower().split()
    if not ref_tokens: return 1.0 if hyp_tokens else 0.0
    return _levenshtein(ref_tokens, hyp_tokens) / len(ref_tokens)

def cer(ref: str, hyp: str) -> float:
    ref_chars = list(ref.replace(" ", "").lower())
    hyp_chars = list(hyp.replace(" ", "").lower())
    if not ref_chars: return 1.0 if hyp_chars else 0.0
    return _levenshtein(ref_chars, hyp_chars) / len(ref_chars)

def jaro_winkler(s1: str, s2: str) -> float:
    """A simplified Jaro-Winkler similarity implementation."""
    def jaro(s1, s2):
        s1_len, s2_len = len(s1), len(s2)
        if s1_len == 0: return 1.0 if s2_len == 0 else 0.0
        match_distance = max(s1_len, s2_len) // 2 - 1
        s1_matches = [False] * s1_len
        s2_matches = [False] * s2_len
        matches = 0
        for i in range(s1_len):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, s2_len)
            for j in range(start, end):
                if not s2_matches[j] and s1[i] == s2[j]:
                    s1_matches[i] = s2_matches[j] = True
                    matches += 1
                    break
        if matches == 0: return 0.0
        transpositions = 0
        k = 0
        for i in range(s1_len):
            if s1_matches[i]:
                while not s2_matches[k]: k += 1
                if s1[i] != s2[k]: transpositions += 1
                k += 1
        return (matches/s1_len + matches/s2_len + (matches - transpositions//2)/matches) / 3

    j = jaro(s1, s2)
    p = 0.1 # prefix scale
    l = 0
    for i in range(min(4, len(s1), len(s2))):
        if s1[i] == s2[i]: l += 1
        else: break
    return j + (l * p * (1 - j))

def semantic_similarity(ref: str, hyp: str) -> float:
    embeddings1 = MODEL.encode(ref, convert_to_tensor=True)
    embeddings2 = MODEL.encode(hyp, convert_to_tensor=True)
    return float(util.cos_sim(embeddings1, embeddings2))

def entity_accuracy(hyp: str, expected_entities: List[str]) -> float:
    if not expected_entities: return 1.0
    found = 0
    for entity in expected_entities:
        if entity.lower() in hyp.lower():
            found += 1
    return found / len(expected_entities)

async def run_evaluation():
    print("\n🚀 Starting Enhanced Sarvam AI Multilingual Evaluation...")
    print("-" * 60)
    
    results = []
    for case in TEST_CASES:
        lang_name, lang_code, source_text = case["language_name"], case["language_code"], case["text"]
        expected_entities = case.get("expected_entities", [])
        output_file = f"eval_output_{lang_code}.wav"
        
        print(f"\n[{lang_name} ({lang_code})]")
        print(f"Target Text: {source_text}")
        
        # 1. TTS
        tts_start = time.time()
        audio_path = await generate_speech(text=source_text, language=lang_code, output_file=output_file)
        tts_latency = round(time.time() - tts_start, 2)
        
        if not audio_path or not os.path.exists(output_file):
            print("❌ TTS Failed.")
            continue
            
        # 2. STT
        stt_start = time.time()
        transcription = transcribe_audio_file(file_path=output_file, language=lang_code)
        stt_latency = round(time.time() - stt_start, 2)
        
        if not transcription:
            print("❌ STT Failed.")
            continue
            
        # Clean transcription (Sarvam might return structured text)
        clean_trans = transcription.split("transcript=")[-1].strip("'\"").split("'")[0].split("\"")[0]
        if "request_id=" in transcription and "transcript=" in transcription:
             # Try regex for more precision if the split is messy
             m = re.search(r"transcript=['\"]([^'\"]+)['\"]", transcription)
             if m: clean_trans = m.group(1)

        # 3. Metrics
        wer_val = wer(source_text, clean_trans)
        cer_val = cer(source_text, clean_trans)
        ser_val = 1.0 if clean_trans.strip() != source_text.strip() else 0.0
        jw_val = jaro_winkler(source_text, clean_trans)
        sem_val = semantic_similarity(source_text, clean_trans)
        ea_val = entity_accuracy(clean_trans, expected_entities)
        
        print(f"✅ STT Result: {clean_trans}")
        print(f"   WER: {wer_val:.3f} | CER: {cer_val:.3f} | JW: {jw_val:.3f}")
        print(f"   Semantic: {sem_val:.3f} | Entity Acc: {ea_val:.1%} | Latency: {stt_latency}s")
        
        if os.path.exists(output_file): os.remove(output_file)
            
        results.append({
            "Language": lang_name,
            "TTS_Latency": tts_latency,
            "STT_Latency": stt_latency,
            "WER": wer_val, "CER": cer_val, "SER": ser_val,
            "JW": jw_val, "Semantic": sem_val, "EA": ea_val,
            "Target": source_text, "Prediction": clean_trans
        })
        
    # Report results to RESULTS.md
    results_md_path = os.path.join(os.path.dirname(__file__), "RESULTS.md")
    with open(results_md_path, "a", encoding="utf-8") as f:
        f.write(f"\n## Enhanced Multilingual Evaluation ({time.strftime('%Y-%m-%d %H:%M:%S')})\n\n")
        f.write("| Lang | WER | CER | JW | Sem Sim | Entity Acc | STT Latency |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for r in results:
            f.write(f"| {r['Language']} | {r['WER']:.3f} | {r['CER']:.3f} | {r['JW']:.3f} | {r['Semantic']:.3f} | {r['EA']:.1%} | {r['STT_Latency']}s |\n")
        
        if results:
            avg_sem = sum(r['Semantic'] for r in results) / len(results)
            avg_ea = sum(r['EA'] for r in results) / len(results)
            f.write(f"\n**Summary Score:** Semantic Similarity: **{avg_sem:.3f}**, Entity Accuracy: **{avg_ea:.1%}**\n")

if __name__ == "__main__":
    if not os.getenv("SARVAM_API_KEY"):
        print("ERROR: SARVAM_API_KEY not found."); exit(1)
    asyncio.run(run_evaluation())
