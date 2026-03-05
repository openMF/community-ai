import os
from dotenv import load_dotenv

# We need to explicitly load a `.env` file since we are in a standalone folder for now.
# This assumes you copy your Sarvam API Key into this local .env file.
load_dotenv()

from sarvam_tools import tool_translate_text

def main():
    print("Testing Sarvam AI Translation Pipeline...")
    
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        print("❌ Error: SARVAM_API_KEY is not set in the environment or .env file.")
        print("Please create a .env file in this directory and add your key.")
        return
        
    print("✓ API Key found.")
    print("-" * 40)
    
    test_text = "Hello, I am testing the new multilingual capabilities of our AI assistant."
    print(f"Original Text (English): {test_text}")
    
    # Test translation to Hindi
    print("\nTranslating to Hindi (hi-IN)...")
    hindi_translation = tool_translate_text(
        text=test_text,
        source_language_code="en-IN",
        target_language_code="hi-IN"
    )
    print(f"Result: {hindi_translation}")
    
    # Test translation to Tamil
    print("\nTranslating to Tamil (ta-IN)...")
    tamil_translation = tool_translate_text(
        text=test_text,
        source_language_code="en-IN",
        target_language_code="ta-IN"
    )
    print(f"Result: {tamil_translation}")

if __name__ == "__main__":
    main()
