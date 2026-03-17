"""
Multilingual Test Dataset Reference for AI-172

Defines which languages + domains to evaluate Deepgram on
Actual audio samples should be sourced from:
- Mifos community recorded samples
- Common Voice dataset for low-resource languages
- Financial domain-specific recordings
"""

# Languages for AI-172 evaluation (priority order)
LANGUAGES = {
    "en": {"name": "English", "native_speakers_billions": 1.5, "priority": 1},
    "fr": {"name": "French", "native_speakers_billions": 0.3, "priority": 3},
    "hi": {"name": "Hindi", "native_speakers_billions": 0.3, "priority": 1},  # High for Mifos
    "pt": {"name": "Portuguese", "native_speakers_billions": 0.25, "priority": 3},
}

# Financial domains for test samples
DOMAINS = [
    "account_opening",      # "I'd like to open a savings account"
    "balance_inquiry",      # "What's my current balance?"
    "money_transfer",       # "Transfer 5000 to my friend's account"
    "loan_inquiry",         # "What are your loan products?"
    "dispute_resolution",   # "I see a charge I don't recognize"
]

# Example reference texts (TODO: expand with real audio)
# In production, these should be paired with actual .wav files
SAMPLE_REFERENCES = {
    "en": [
        "I would like to open a savings account with your bank",
        "What is my current account balance",
        "I need to transfer five thousand rupees",
    ],
    "hi": [
        "Main aapke bank ke saath ek bachat khata khulna chahta hoon",
        "Mera current balance kya hai",
        "Mujhe paanch hazaar rupaye transfer karne hain",
    ],
}

def get_languages():
    """Get list of languages to evaluate"""
    return sorted(LANGUAGES.items(), key=lambda x: x[1]["priority"])

def get_domains():
    """Get financial domains to test"""
    return DOMAINS

def get_sample_references():
    """Get reference texts for each language"""
    return SAMPLE_REFERENCES
