import os
import logging
from dotenv import load_dotenv

def setup_logger(name: str = "speech_benchmarking") -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)

def load_env_vars():
    # Load .env from root or specific paths if needed
    load_dotenv()
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        print("WARNING: SARVAM_API_KEY not found in environment.")
    return api_key
