import re
import json
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import os
import spacy
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load intent configuration
INTENT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/intent_patterns.json')

with open(INTENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
    INTENT_PATTERNS = json.load(f)

# Supported languages with their models
LANGUAGE_MODELS = {
    'en-US': 'en_core_web_sm',
    'hi-IN': 'xx_ent_wiki_sm',  # Spacy's multilingual model for Hindi
    # Add more language models as needed
}

# Load NLP models for each language
nlp_models = {}

# Hindi number words mapping
HINDI_NUMBER_WORDS = {
    'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5, 'छह': 6, 'सात': 7, 'आठ': 8, 'नौ': 9, 'दस': 10,
    'ग्यारह': 11, 'बारह': 12, 'तेरह': 13, 'चौदह': 14, 'पंद्रह': 15, 'सोलह': 16, 'सत्रह': 17, 'अठारह': 18, 'उन्नीस': 19, 'बीस': 20,
    'तीस': 30, 'चालीस': 40, 'पचास': 50, 'साठ': 60, 'सत्तर': 70, 'अस्सी': 80, 'नब्बे': 90,
    'सौ': 100, 'हजार': 1000, 'लाख': 100000, 'करोड़': 10000000
}

def preprocess_text(text):
    """
    Preprocess text to remove any special formatting 
    like <s> tags that might be added during speech recognition
    """
    # Remove <s> tags that might be present in speech recognition output
    text = re.sub(r'<s>', '', text)
    # Remove any other potential artifacts
    text = re.sub(r'</s>', '', text)
    return text

def load_nlp_model(language):
    """Load the appropriate NLP model for the language if not already loaded."""
    if language not in nlp_models:
        model_name = LANGUAGE_MODELS.get(language, LANGUAGE_MODELS.get('en-US'))
        try:
            nlp_models[language] = spacy.load(model_name)
        except OSError:
            # If model isn't available, download it (not recommended in production)
            spacy.cli.download(model_name)
            nlp_models[language] = spacy.load(model_name)
    return nlp_models[language]

def extract_intent(text, language='en-US'):
    """
    Extract banking intent from the recognized speech text.
    Returns the intent type and relevant parameters.
    """
    if not text:
        logger.warning("Empty text provided for intent extraction")
        return {'intent_type': 'unknown', 'parameters': {}}
    
    # Preprocess the text to remove any special formatting tags
    text = preprocess_text(text)
        
    # Normalize text - lowercase and remove extra spaces
    normalized_text = ' '.join(text.lower().split())
    
    logger.info(f"Preprocessed text for intent matching: '{normalized_text}'")
    
    # Load the appropriate NLP model
    try:
        nlp = load_nlp_model(language)
        
        # Process the text
        doc = nlp(normalized_text)
    except Exception as e:
        logger.error(f"Error processing text with NLP model: {str(e)}")
        doc = None
    
    # Initialize intent data
    intent_data = {
        'intent_type': 'unknown',
        'parameters': {}
    }
    
    # Check for patterns in the text based on the language
    language_patterns = INTENT_PATTERNS.get(language, INTENT_PATTERNS.get('en-US'))
    
    logger.info(f"Matching intent for: '{normalized_text}'")
    
    # Try pattern matching first
    for intent, patterns in language_patterns.items():
        for pattern in patterns['patterns']:
            # For non-English languages, try more flexible matching
            if language != 'en-US':
                # Count matching words instead of exact pattern for non-Latin script languages
                pattern_words = set(pattern.lower().split())
                text_words = set(normalized_text.split())
                common_words = pattern_words.intersection(text_words)
                
                # If more than 50% of pattern words are in the text, consider it a match
                if len(common_words) >= len(pattern_words) * 0.5:
                    logger.info(f"Flexible match for pattern '{pattern}' in language {language}")
                    intent_data['intent_type'] = intent
                    
                    # Extract parameters like amounts, accounts, etc.
                    if intent == 'transfer_money':
                        # Extract amount for all languages (numbers are usually the same)
                        amount_matches = re.findall(r'(\d+(?:\.\d+)?)', normalized_text)
                        if amount_matches:
                            intent_data['parameters']['amount'] = float(amount_matches[0])
                        
                        # Extract Hindi number words (like सौ = 100)
                        if language == 'hi-IN':
                            extract_hindi_parameters(normalized_text, intent_data)
                    
                    return intent_data
                    
            # Traditional regex pattern matching as fallback
            if re.search(pattern, normalized_text):
                logger.info(f"Matched pattern '{pattern}' for intent '{intent}'")
                intent_data['intent_type'] = intent
                
                # Extract parameters like amounts, accounts, etc.
                if intent == 'check_balance':
                    # No additional parameters needed
                    pass
                
                elif intent == 'transfer_money':
                    # Extract amount
                    amount_matches = re.findall(r'(\d+(?:\.\d+)?)', normalized_text)
                    if amount_matches:
                        intent_data['parameters']['amount'] = float(amount_matches[0])
                    
                    # Extract Hindi number words and recipient for Hindi
                    if language == 'hi-IN':
                        extract_hindi_parameters(normalized_text, intent_data)
                    
                    # Extract recipient for English - simplified approach for demo
                    if language == 'en-US':
                        recipient_matches = re.findall(r'to\s+(\w+)', normalized_text)
                        if recipient_matches:
                            intent_data['parameters']['recipient'] = recipient_matches[0]
                
                elif intent == 'transaction_history':
                    # Extract time period if mentioned
                    if 'last month' in normalized_text:
                        intent_data['parameters']['period'] = 'last_month'
                    elif 'last week' in normalized_text:
                        intent_data['parameters']['period'] = 'last_week'
                    else:
                        intent_data['parameters']['period'] = 'recent'
                
                return intent_data
    
    # If no pattern matched, try keyword matching as fallback
    if intent_data['intent_type'] == 'unknown' and doc is not None:
        # Define keywords for different languages
        keywords = {
            'en-US': {
                'check_balance': ['balance', 'money', 'account', 'bank', 'have', 'much'],
                'transfer_money': ['transfer', 'send', 'pay', 'give'],
                'transaction_history': ['transaction', 'history', 'recent', 'activity']
            },
            'hi-IN': {
                'check_balance': ['बैलेंस', 'पैसा', 'खाता', 'बैंक', 'शेष', 'बताओ', 'दिखाओ', 'कितना'],
                'transfer_money': ['भेजो', 'ट्रांसफर', 'भुगतान', 'दो', 'भेजें', 'भेजिए', 'रुपया', 'रुपये', 'को'],
                'transaction_history': ['लेनदेन', 'इतिहास', 'हाल', 'गतिविधि']
            },
            'ta-IN': {
                'check_balance': ['இருப்பு', 'பணம்', 'கணக்கு', 'வங்கி', 'காட்டு'],
                'transfer_money': ['அனுப்பு', 'பரிமாற்றம்', 'செலுத்து'],
                'transaction_history': ['பரிவர்த்தனை', 'வரலாறு', 'சமீபத்திய']
            }
        }
        
        # Use the appropriate language keywords or default to English
        lang_keywords = keywords.get(language, keywords['en-US'])
        text_tokens = [token.text for token in doc]
        
        # Count keyword occurrences
        intent_scores = {}
        for intent, kw_list in lang_keywords.items():
            intent_scores[intent] = sum(1 for word in text_tokens if word in kw_list)
        
        # Determine intent by highest keyword match count
        if any(intent_scores.values()):  # Only if we found any keywords
            max_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[max_intent] > 0:
                logger.info(f"Matched intent '{max_intent}' via keyword count: {intent_scores}")
                intent_data['intent_type'] = max_intent
                
                # For transfer_money intent, try to extract parameters
                if max_intent == 'transfer_money':
                    # Extract Hindi parameters if in Hindi
                    if language == 'hi-IN':
                        extract_hindi_parameters(normalized_text, intent_data)
    
    logger.info(f"Final detected intent: {intent_data['intent_type']}")
    if 'parameters' in intent_data:
        logger.info(f"Extracted parameters: {intent_data['parameters']}")
    return intent_data

def extract_hindi_parameters(text, intent_data):
    """Extract amount and recipient from Hindi text"""
    # Extract recipient by looking for words before "को"
    ko_matches = re.findall(r'([\u0900-\u097F\w]+)\s+को', text)
    if ko_matches:
        intent_data['parameters']['recipient'] = ko_matches[0]
        logger.info(f"Found Hindi recipient: {ko_matches[0]}")
    
    # Extract Hindi number words for amount - check for compound numbers
    # First scan the text for all Hindi number words
    found_numbers = []
    text_words = text.split()
    for i, word in enumerate(text_words):
        if word in HINDI_NUMBER_WORDS:
            found_numbers.append((i, word, HINDI_NUMBER_WORDS[word]))
    
    if found_numbers:
        # Process found numbers
        if len(found_numbers) == 1:
            # Single number word
            intent_data['parameters']['amount'] = float(found_numbers[0][2])
            logger.info(f"Found Hindi number word: {found_numbers[0][1]} = {found_numbers[0][2]}")
        else:
            # Check for compound numbers like "दो सौ" (two hundred)
            found_numbers.sort(key=lambda x: x[0])  # Sort by position in text
            total = 0
            current_value = 0
            
            for i, (pos, word, value) in enumerate(found_numbers):
                if value >= 100:  # For सौ (100), हजार (1000), etc.
                    if current_value == 0:
                        current_value = value
                    else:
                        current_value *= value
                    
                    if i == len(found_numbers)-1 or found_numbers[i+1][2] < 100:
                        total += current_value
                        current_value = 0
                else:
                    if i < len(found_numbers)-1 and found_numbers[i+1][2] >= 100:
                        current_value = value  # Store for multiplication with next number
                    else:
                        total += value
            
            # Add any remaining value
            if current_value > 0:
                total += current_value
                
            intent_data['parameters']['amount'] = float(total)
            number_words = ' '.join(word for _, word, _ in found_numbers)
            logger.info(f"Found compound Hindi number: {number_words} = {total}")
    
    # If we couldn't extract the amount from number words, try digits
    if 'amount' not in intent_data['parameters']:
        amount_matches = re.findall(r'(\d+(?:\.\d+)?)', text)
        if amount_matches:
            intent_data['parameters']['amount'] = float(amount_matches[0])
            logger.info(f"Found numeric amount: {amount_matches[0]}")
