"""
Test script for the Voice-Driven Banking via LAMs POC

This script tests the core functionality of the system including:
- Speech recognition
- Intent detection
- Banking operations

Usage:
    python test.py

Prerequisites:
    - All dependencies installed (pip install -r requirements.txt)
    - The mock database has been created (run the app once)
"""

import os
import json
from models.speech_recognition import recognize_speech
from models.intent_recognition import extract_intent
from services.banking_service import process_banking_request
from services.user_service import get_user_by_id, load_users_db

# Test data
TEST_AUDIO_DIR = 'test_data'
os.makedirs(TEST_AUDIO_DIR, exist_ok=True)

def test_intent_recognition():
    """Test the intent recognition system with text input."""
    print("\n--- Testing Intent Recognition ---")
    
    test_phrases = {
        'en-US': [
            "What is my account balance?",
            "Transfer 100 dollars to Jane",
            "Show my recent transactions"
        ],
        'hi-IN': [
            "मेरा बैलेंस क्या है",
            "जेन को 100 रुपये ट्रांसफर करें",
            "मेरे हाल के लेनदेन दिखाएं"
        ],
        'sw': [
            "Salio langu ni nini",
            "Tuma shilingi 100 kwa Jane",
            "Nionyeshe miamala yangu ya hivi karibuni"
        ]
    }
    
    expected_intents = ['check_balance', 'transfer_money', 'transaction_history']
    
    for language, phrases in test_phrases.items():
        print(f"\nLanguage: {language}")
        for i, phrase in enumerate(phrases):
            intent_data = extract_intent(phrase, language)
            expected = expected_intents[i]
            result = "✓" if intent_data['intent_type'] == expected else "✗"
            print(f"{result} \"{phrase}\" → {intent_data['intent_type']}")
            
            # Print parameters for transfer_money intent
            if intent_data['intent_type'] == 'transfer_money' and 'parameters' in intent_data:
                print(f"   Parameters: {json.dumps(intent_data['parameters'])}")

def test_banking_operations():
    """Test banking operations with the mock database."""
    print("\n--- Testing Banking Operations ---")
    
    # Load a test user
    users = load_users_db()
    user = users.get('1')  # John Doe
    
    if not user:
        print("Error: Test user not found. Please run the app once to create mock data.")
        return
    
    # Test balance check
    balance_intent = {'intent_type': 'check_balance', 'parameters': {}}
    balance_response = process_banking_request(balance_intent, user)
    
    print("\nBalance Check:")
    print(f"Success: {balance_response['success']}")
    print(f"Message: {balance_response['message']}")
    
    # Test transaction history
    history_intent = {'intent_type': 'transaction_history', 'parameters': {'period': 'recent'}}
    history_response = process_banking_request(history_intent, user)
    
    print("\nTransaction History:")
    print(f"Success: {history_response['success']}")
    print(f"Message: {history_response['message']}")
    print(f"Transactions: {len(history_response.get('transactions', []))}")
    
    # Test money transfer (if Jane exists)
    recipient_exists = any('jane' in u['name'].lower() for u in users.values())
    
    if recipient_exists:
        transfer_intent = {
            'intent_type': 'transfer_money', 
            'parameters': {'amount': 50.0, 'recipient': 'Jane'}
        }
        transfer_response = process_banking_request(transfer_intent, user)
        
        print("\nMoney Transfer:")
        print(f"Success: {transfer_response['success']}")
        print(f"Message: {transfer_response['message']}")

def run_tests():
    """Run all the tests."""
    print("=== Voice-Driven Banking System Tests ===")
    
    # Test intent recognition
    test_intent_recognition()
    
    # Test banking operations
    test_banking_operations()
    
    print("\nTests completed.")

if __name__ == "__main__":
    run_tests()
