import asyncio
import time
import os
from dotenv import load_dotenv

# Import the Sarvam utility functions
from sarvam_tts import generate_speech
from sarvam_stt import transcribe_audio_file

load_dotenv()

BANKING_TEST_CASES = [
    {
        "language_name": "English",
        "language_code": "en",
        "expected": "show my loan balance",
        "audio_path": "datasets/english_audio/sample1.wav"
    },
    {
        "language_name": "Hindi",
        "language_code": "hi",
        "expected": "mera loan balance batao",
        "audio_path": "datasets/hindi_audio/sample1.wav"
    },
    {
        "language_name": "English",
        "language_code": "en",
        "expected": "debit two hundred from arpit's account",
        "audio_path": "datasets/english_audio/sample3.wav"
    },
    {
        "language_name": "Hindi",
        "language_code": "hi",
        "expected": "arpit ke account se do sau rupaye kaato",
        "audio_path": "datasets/hindi_audio/sample3.wav"
    },
    {
        "language_name": "English",
        "language_code": "en",
        "expected": "credit one thousand to my savings account",
        "audio_path": "datasets/english_audio/sample4.wav"
    },
    {
        "language_name": "Hindi",
        "language_code": "hi",
        "expected": "mere savings account mein ek hazaar rupaye dalo",
        "audio_path": "datasets/hindi_audio/sample4.wav"
    },
    {
        "language_name": "English",
        "language_code": "en",
        "expected": "transfer 500 to sanya",
        "audio_path": "datasets/english_audio/sample5.wav"
    }
]

def _levenshtein(a, b):
    """Compute Levenshtein distance between sequences a and b."""
    la = len(a)
    lb = len(b)
    if la == 0: return lb
    if lb == 0: return la
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
    ref_tokens = ref.strip().lower().split()
    hyp_tokens = hyp.strip().lower().split()
    if len(ref_tokens) == 0:
        return 1.0 if len(hyp_tokens) > 0 else 0.0
    dist = _levenshtein(ref_tokens, hyp_tokens)
    return dist / len(ref_tokens)

async def run_banking_evaluation():
    print("🚀 Running Banking-Specific Sarvam AI Evaluation...")
    print("-" * 50)
    
    # Ensure dataset directories exist for simulation
    os.makedirs("datasets/english_audio", exist_ok=True)
    os.makedirs("datasets/hindi_audio", exist_ok=True)
    os.makedirs("datasets/tamil_audio", exist_ok=True)
    os.makedirs("datasets/bengali_audio", exist_ok=True)
    os.makedirs("datasets/punjabi_audio", exist_ok=True)

    for case in BANKING_TEST_CASES:
        lang_code = case["language_code"]
        expected_text = case["expected"]
        audio_file = case["audio_path"]
        
        # 1. Generate audio using TTS (to simulate the missing dataset)
        # In a real scenario, these files would already exist.
        if not os.path.exists(audio_file):
            print(f"Generating sample audio for: '{expected_text}' ({lang_code})")
            await generate_speech(text=expected_text, language=lang_code, output_file=audio_file)
        
        if not os.path.exists(audio_file):
            print(f"❌ Failed to generate/find audio: {audio_file}")
            continue

        # 2. Transcribe using STT
        predicted_text = transcribe_audio_file(file_path=audio_file, language=lang_code) or ""
        
        # 3. Calculate WER
        error_rate = wer(expected_text, predicted_text)
        
        # 4. Print in requested format
        print(f"Audio: {audio_file}")
        print(f"Expected: {expected_text}")
        print(f"Predicted:  {predicted_text}")
        print(f"WER: {error_rate:.2f}")
        print("-" * 5)

if __name__ == "__main__":
    if not os.getenv("SARVAM_API_KEY"):
        print("ERROR: SARVAM_API_KEY environment variable not found.")
        exit(1)
        
    asyncio.run(run_banking_evaluation())
