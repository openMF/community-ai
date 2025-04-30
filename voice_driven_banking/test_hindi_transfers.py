"""
Test script for Hindi money transfer intent recognition

This script tests the Hindi money transfer intent detection with various phrases
"""

import json
from models.intent_recognition import extract_intent

def test_hindi_transfers():
    """Test Hindi money transfer intent recognition with various phrases."""
    print("\n=== Testing Hindi Money Transfer Intent Recognition ===\n")
    
    test_phrases = [
        "जॉन को सौ रुपये भेजिए",            # Send 100 rupees to John
        "राम को दो सौ रुपये ट्रांसफर करें",  # Transfer 200 rupees to Ram
        "सीता को हजार रुपया भेज दीजिए",     # Send 1000 rupees to Sita
        "अनिल को पांच सौ भेजो"              # Send 500 to Anil
    ]
    
    for phrase in test_phrases:
        intent_data = extract_intent(phrase, 'hi-IN')
        print(f"Phrase: \"{phrase}\"")
        print(f"Detected Intent: {intent_data['intent_type']}")
        print(f"Parameters: {json.dumps(intent_data.get('parameters', {}), ensure_ascii=False)}")
        print("-" * 50)

if __name__ == "__main__":
    test_hindi_transfers()
