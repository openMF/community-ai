import asyncio
import time
import os
from dotenv import load_dotenv

# We need to simulate the imports as they exist in the module
from sarvam_tts import generate_speech
from sarvam_stt import transcribe_audio_file

load_dotenv()

TEST_CASES = [
    {
        "language_name": "Hindi",
        "language_code": "hi",
        "text": "आपका स्वागत है! यह एक परीक्षण संदेश है।"
    },
    {
        "language_name": "Bengali",
        "language_code": "bn",
        "text": "স্বাগতম! এটি একটি পরীক্ষামূলক বার্তা।"
    },
    {
        "language_name": "Tamil",
        "language_code": "ta",
        "text": "வரவேற்கிறோம்! இது ஒரு சோதனை செய்தி."
    },
    {
        "language_name": "Punjabi",
        "language_code": "pa",
        "text": "ਜੀ ਆਇਆਂ ਨੂੰ! ਇਹ ਇੱਕ ਟੈਸਟ ਸੁਨੇਹਾ ਹੈ।"
    }
]


def _levenshtein(a, b):
    """Compute Levenshtein distance between sequences a and b."""
    # a and b can be lists (for WER) or strings (for CER)
    la = len(a)
    lb = len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        dp[i][0] = i
    for j in range(lb + 1):
        dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,    # deletion
                dp[i][j - 1] + 1,    # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )
    return dp[la][lb]


def wer(ref, hyp):
    """Compute Word Error Rate between reference and hypothesis strings."""
    ref_tokens = ref.strip().split()
    hyp_tokens = hyp.strip().split()
    if len(ref_tokens) == 0:
        return 1.0 if len(hyp_tokens) > 0 else 0.0
    dist = _levenshtein(ref_tokens, hyp_tokens)
    return dist / len(ref_tokens)


def cer(ref, hyp):
    """Compute Character Error Rate between reference and hypothesis strings."""
    ref_chars = list(ref.replace(" ", ""))
    hyp_chars = list(hyp.replace(" ", ""))
    if len(ref_chars) == 0:
        return 1.0 if len(hyp_chars) > 0 else 0.0
    dist = _levenshtein(ref_chars, hyp_chars)
    return dist / len(ref_chars)

async def run_evaluation():
    print("🚀 Starting Sarvam AI Multilingual Evaluation...")
    print("-" * 50)
    
    results = []

    for case in TEST_CASES:
        lang_name = case["language_name"]
        lang_code = case["language_code"]
        source_text = case["text"]
        output_file = f"eval_output_{lang_code}.wav"
        
        print(f"\n[{lang_name} ({lang_code})]")
        print(f"Target Text: {source_text}")
        
        # 1. Test TTS
        tts_start = time.time()
        print(f"Synthesizing speech via Bulbul v3...")
        # Awaiting because generate_speech is an async function
        audio_path = await generate_speech(text=source_text, language=lang_code, output_file=output_file)
        tts_end = time.time()
        tts_latency = round(tts_end - tts_start, 2)
        
        if not audio_path or not os.path.exists(output_file):
            print("❌ TTS Failed.")
            continue
            
        print(f"✅ TTS Success ({tts_latency}s)")
        
        # 2. Test STT
        stt_start = time.time()
        print(f"Transcribing {output_file} via Saaras v3...")
        transcription = transcribe_audio_file(file_path=output_file, language=lang_code)
        stt_end = time.time()
        stt_latency = round(stt_end - stt_start, 2)
        
        if not transcription:
            print("❌ STT Failed.")
            continue
            
        print(f"✅ STT Success ({stt_latency}s)")
        print(f"Result: {transcription[:100]}...") # Print first 100 chars
        # Compute WER and CER
        wer_score = wer(source_text, transcription)
        cer_score = cer(source_text, transcription)
        print(f"WER: {wer_score:.3f}, CER: {cer_score:.3f}")
        
        # Cleanup
        if os.path.exists(output_file):
            os.remove(output_file)
            
        # Record successful metric
        results.append({
            "Language": lang_name,
            "TTS_Latency_Seconds": tts_latency,
            "STT_Latency_Seconds": stt_latency,
            "WER": wer_score,
            "CER": cer_score,
            "Target_Text": source_text,
            "Transcription": transcription,
            "Success": True
        })
        
    print("\n" + "="*50)
    print("📊 Evaluation Summary:")
    print(f"Total Languages Tested: {len(TEST_CASES)}")
    print(f"Successful Pipelines: {len(results)}")
    
    for r in results:
        print(f"- {r['Language']}: TTS={r['TTS_Latency_Seconds']}s, STT={r['STT_Latency_Seconds']}s, WER={r['WER']:.3f}, CER={r['CER']:.3f}")

    # Append results to RESULTS.md
    results_md_path = os.path.join(os.path.dirname(__file__), "RESULTS.md")
    try:
        with open(results_md_path, "a", encoding="utf-8") as f:
            f.write("\n## Multilingual Evaluation Results\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            total_wer = 0.0
            total_cer = 0.0
            for r in results:
                f.write(f"- **{r['Language']}**:\n")
                f.write(f"  - Target: {r['Target_Text']}\n")
                f.write(f"  - Transcription: {r['Transcription']}\n")
                f.write(f"  - TTS latency (s): {r['TTS_Latency_Seconds']}\n")
                f.write(f"  - STT latency (s): {r['STT_Latency_Seconds']}\n")
                f.write(f"  - WER: {r['WER']:.3f}\n")
                f.write(f"  - CER: {r['CER']:.3f}\n\n")
                total_wer += r['WER']
                total_cer += r['CER']
            if len(results) > 0:
                avg_wer = total_wer / len(results)
                avg_cer = total_cer / len(results)
                f.write(f"**Average WER:** {avg_wer:.3f}\n")
                f.write(f"**Average CER:** {avg_cer:.3f}\n")
    except Exception as e:
        print(f"Failed to write results to {results_md_path}: {e}")

if __name__ == "__main__":
    if not os.getenv("SARVAM_API_KEY"):
        print("ERROR: SARVAM_API_KEY environment variable not found.")
        exit(1)
        
    asyncio.run(run_evaluation())
