import os
import shutil
import json

def organize_for_hf(export_dir="hf_raw_upload"):
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.makedirs(export_dir)
    
    # We'll create a single folder for all files to make them easy to browse
    audio_dir = os.path.join(export_dir, "audio")
    text_dir = os.path.join(export_dir, "text")
    os.makedirs(audio_dir)
    os.makedirs(text_dir)
    
    metadata_path = "dataset/metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    jsonl_data = []
    
    for item in metadata:
        src_audio = item["audio_path"]
        src_text = item["text_path"]
        
        # New paths relative to export_dir
        filename = os.path.basename(src_audio)
        basename = os.path.splitext(filename)[0]
        
        dest_audio = os.path.join(audio_dir, filename)
        dest_text = os.path.join(text_dir, f"{basename}.txt")
        
        if os.path.exists(src_audio):
            shutil.copy(src_audio, dest_audio)
        if os.path.exists(src_text):
            shutil.copy(src_text, dest_text)
            
        jsonl_data.append({
            "id": item["id"],
            "language_name": item["language_name"],
            "language_code": item["language_code"],
            "text": item["text"],
            "expected_entities": item["expected_entities"],
            "audio": f"audio/{filename}"
        })
    
    # Save the metadata.jsonl in the root for the 'datasets' library
    with open(os.path.join(export_dir, "metadata.jsonl"), "w", encoding="utf-8") as f:
        for entry in jsonl_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"Organized 80 samples into {export_dir}")

if __name__ == "__main__":
    organize_for_hf()
