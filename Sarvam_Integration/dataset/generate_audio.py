import os
import json
import asyncio
from providers.sarvam import SarvamProvider
from utils.helpers import setup_logger, load_env_vars

logger = setup_logger(__name__)

async def generate_audio_dataset(metadata_path: str = "dataset/metadata.json", output_dir: str = "dataset"):
    load_env_vars()
    provider = SarvamProvider()
    
    if not os.path.exists(metadata_path):
        logger.error(f"Metadata file {metadata_path} not found.")
        return

    with open(metadata_path, "r") as f:
        metadata = json.load(f)
        
    logger.info(f"Generating audio and text files for {len(metadata)} items...")
    
    for item in metadata:
        text = item["text"]
        lang = item["language_code"]
        lang_name = item["language_name"].lower()
        
        # Structure: dataset/hindi_audio/hi_bal_01.wav and hi_bal_01.txt
        lang_dir = os.path.join(output_dir, f"{lang_name}_audio")
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)
            
        file_id = item["id"]
        audio_path = os.path.join(lang_dir, f"{file_id}.wav")
        text_path = os.path.join(lang_dir, f"{file_id}.txt")
        
        # Save Text File
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"Saved text ground truth to {text_path}")
        
        # Generate Audio File if not exists
        if os.path.exists(audio_path):
            logger.info(f"Skipping {file_id}.wav, already exists.")
            item["audio_path"] = audio_path
            item["text_path"] = text_path
            continue
            
        logger.info(f"Generating audio for {file_id} ({lang}) -> {audio_path}...")
        result = provider.text_to_speech(text, lang, audio_path)
        
        if result:
            logger.info(f"Successfully generated {audio_path}")
            item["audio_path"] = audio_path
            item["text_path"] = text_path
        else:
            logger.error(f"Failed to generate audio for {file_id}")

    # Update metadata with audio and text paths
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info("Metadata updated with audio and text paths.")

if __name__ == "__main__":
    asyncio.run(generate_audio_dataset())
