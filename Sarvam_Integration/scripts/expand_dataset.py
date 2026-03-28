import json
import os
import asyncio
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.sarvam import SarvamProvider
from utils.helpers import load_env_vars

ENGLISH_PHRASES = [
    {"id": "en_bal_01", "text": "What is my current account balance?", "entities": ["current account", "balance"]},
    {"id": "en_sav_01", "text": "I want to open a new savings account.", "entities": ["savings account"]},
    {"id": "en_loan_01", "text": "How can I apply for a personal loan?", "entities": ["personal loan"]},
    {"id": "en_fd_01", "text": "What are the interest rates for a fixed deposit?", "entities": ["fixed deposit", "interest rates"]},
    {"id": "en_card_01", "text": "I need to block my credit card immediately.", "entities": ["credit card", "block"]},
    {"id": "en_tra_01", "text": "Transfer five thousand rupees to my sister's account.", "entities": ["five thousand rupees", "transfer"]},
    {"id": "en_atm_01", "text": "Where is the nearest ATM located?", "entities": ["ATM"]},
    {"id": "en_home_01", "text": "What documents are needed for a home loan?", "entities": ["home loan", "documents"]},
    {"id": "en_mob_01", "text": "I want to update my mobile number in the bank records.", "entities": ["mobile number", "update"]},
    {"id": "en_trans_01", "text": "Show me my last five transactions.", "entities": ["last five transactions"]},
    {"id": "en_act_01", "text": "How do I activate mobile banking?", "entities": ["activate", "mobile banking"]},
    {"id": "en_gold_01", "text": "What is the process for a gold loan?", "entities": ["gold loan", "process"]},
    {"id": "en_close_01", "text": "I want to close my current account.", "entities": ["close", "current account"]},
    {"id": "en_stat_01", "text": "Can I get a bank statement for the last six months?", "entities": ["bank statement", "last six months"]},
    {"id": "en_sal_01", "text": "What is the minimum balance for a salary account?", "entities": ["minimum balance", "salary account"]}
]

LANGUAGES = [
    {"name": "Hindi", "code": "hi-IN", "iso": "hi"},
    {"name": "Bengali", "code": "bn-IN", "iso": "bn"},
    {"name": "Tamil", "code": "ta-IN", "iso": "ta"},
    {"name": "Telugu", "code": "te-IN", "iso": "te"},
    {"name": "Marathi", "code": "mr-IN", "iso": "mr"},
    {"name": "Kannada", "code": "kn-IN", "iso": "kn"},
    {"name": "Gujarati", "code": "gu-IN", "iso": "gu"}
]

async def expand_dataset():
    load_env_vars()
    provider = SarvamProvider()
    
    expanded_data = []
    
    # Add English phrases first
    print("Adding English phrases (first 10)...")
    for phrase in ENGLISH_PHRASES[:10]:
        expanded_data.append({
            "id": phrase["id"],
            "language_name": "English",
            "language_code": "en",
            "text": phrase["text"],
            "expected_entities": phrase["entities"],
            "audio_path": f"dataset/english_audio/{phrase['id']}.wav",
            "text_path": f"dataset/english_audio/{phrase['id']}.txt"
        })
    
    # Translate and add other languages (10 per language)
    for lang in LANGUAGES:
        print(f"Translating 10 phrases for {lang['name']}...")
        for phrase in ENGLISH_PHRASES[:10]:
            translated_text = None
            retries = 3
            while retries > 0 and not translated_text:
                translated_text = provider.translate(
                    text=phrase["text"],
                    source_lang="en-IN",
                    target_lang=lang["code"]
                )
                if not translated_text:
                    print(f"Rate limited or failed. Retrying... ({retries} left)")
                    import time
                    time.sleep(2)
                    retries -= 1
            
            if translated_text:
                lang_dir = f"{lang['name'].lower()}_audio"
                item_id = phrase["id"].replace("en_", f"{lang['iso']}_")
                
                expanded_data.append({
                    "id": item_id,
                    "language_name": lang["name"],
                    "language_code": lang["iso"],
                    "text": translated_text,
                    "expected_entities": phrase["entities"],
                    "audio_path": f"dataset/{lang_dir}/{item_id}.wav",
                    "text_path": f"dataset/{lang_dir}/{item_id}.txt"
                })
            else:
                print(f"Failed to translate {phrase['id']} to {lang['name']} after retries")

    output_path = "dataset/metadata.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(expanded_data, f, ensure_ascii=False, indent=2)
    
    print(f"Done! Created expanded dataset with {len(expanded_data)} samples at {output_path}")

if __name__ == "__main__":
    asyncio.run(expand_dataset())
