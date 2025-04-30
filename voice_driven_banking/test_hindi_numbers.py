"""
Test script for Hindi number parsing in banking commands

This script tests the enhanced Hindi number parsing functionality
"""

import json
from models.intent_recognition import extract_intent

def test_hindi_numbers():
    """Test parsing different Hindi number formats in money transfer commands."""
    print("\n=== Testing Hindi Number Parsing ===\n")
    
    test_phrases = [
        "जॉन को सौ रुपये भेजिए",             # 100 rupees to John
        "राम को दो सौ रुपये भेजें",           # 200 rupees to Ram
        "सीता को एक हजार रुपया भेजें",        # 1000 rupees to Sita
        "अनिल को पांच सौ रुपये ट्रांसफर करें", # 500 rupees to Anil
        "मोहन को पचास रुपये भेजिए",          # 50 rupees to Mohan
        "राधा को दो हजार पांच सौ भेजें",      # 2500 rupees to Radha
        "विकास को 100 रुपये भेजो",            # 100 rupees (numeric) to Vikas
        "संजय को एक सौ बीस रुपये भेज दो"      # 120 rupees to Sanjay
    ]
    
    for phrase in test_phrases:
        intent_data = extract_intent(phrase, 'hi-IN')
        print(f"Phrase: \"{phrase}\"")
        print(f"Detected Intent: {intent_data['intent_type']}")
        print(f"Parameters: {json.dumps(intent_data.get('parameters', {}), ensure_ascii=False)}")
        print("-" * 50)

if __name__ == "__main__":
    test_hindi_numbers()
