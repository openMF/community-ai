# Voice-Driven Banking via LAMs

A proof-of-concept for a voice-based banking platform supporting multiple languages including low-resource languages and dialects.

## Project Overview

This project demonstrates how Large Acoustic Models (LAMs) can be utilized to create an inclusive, voice-controlled banking system that works with languages that are typically underserved by mainstream voice recognition technologies.

### Key Features

- **Multilingual Speech Recognition**: Supports English, Hindi, and Tamil (extendable to other languages)
- **Intent Recognition**: Identifies banking operations such as balance checks, money transfers, and transaction history requests
- **Voice Biometrics**: Simple voice authentication system for security
- **Banking Operations**: Basic simulation of banking functionality
- **Responsive UI**: Web interface for interacting with the voice banking system

## Technology Stack

- **Backend**: Python, Flask
- **Speech Recognition**: SpeechRecognition, Wav2Vec2 (for low-resource languages)
- **NLP**: spaCy, regex-based intent detection
- **Voice Biometrics**: Gaussian Mixture Models with MFCC features
- **Frontend**: HTML, CSS, JavaScript
- **Data Storage**: Simple JSON-based storage (for demonstration purposes)

## Installation

### Prerequisites

- Miniconda or Anaconda
- A modern web browser

### Setup with Miniconda

1. Install Miniconda:
   - [Download Miniconda](https://docs.conda.io/en/latest/miniconda.html)
   - Follow the installation instructions for your operating system

2. Clone the repository:
   ```
   git clone <repository-url>
   cd GSoC'25 Mifos POC
   ```

3. Create and activate the conda environment:
   ```
   conda env create -f environment.yml
   conda activate voice-banking
   ```

4. Download required language models for spaCy:
   ```
   python -m spacy download en_core_web_sm
   python -m spacy download xx_ent_wiki_sm
   ```

5. (Alternative) If you prefer using pip instead of conda environment:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

3. Register a new account or log in with the demo accounts:
   - Username: `johndoe`, Password: `password123` (English)
   - Username: `janesmith`, Password: `password456` (Hindi)

## Usage Guide

### Voice Commands

The system supports the following banking operations:

1. **Check Balance**
   - English: "What is my balance?", "Check my account balance"
   - Hindi: "मेरा बैलेंस क्या है", "मेरा बैलेंस दिखाएं"
   - Tamil: "என் இருப்பு என்ன", "என் கணக்கு இருப்பு காட்டு"

2. **Transfer Money**
   - English: "Transfer 100 dollars to Jane", "Send 50 to John"
   - Hindi: "जेन को 100 रुपये ट्रांसफर करें"
   - Tamil: "ஜேனுக்கு 100 ரூபாய் அனுப்பு"

3. **Transaction History**
   - English: "Show my recent transactions", "Show my transaction history"
   - Hindi: "मेरे हाल के लेनदेन दिखाएं"
   - Tamil: "என் சமீபத்திய பரிவர்த்தனைகளைக் காட்டு"

### Voice Authentication

Upon first use, the system will automatically enroll your voice. For subsequent uses, it will authenticate your voice against the stored voiceprint. In this proof-of-concept, authentication thresholds are set low for ease of demonstration.

## Project Structure

```
/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── /config/
│   └── intent_patterns.json # Language-specific patterns for intent recognition
├── /data/
│   ├── mock_db.json        # Mock banking data (auto-generated)
│   ├── users.json          # User data (auto-generated)
│   └── /voice_prints/      # Voice authentication models (auto-generated)
├── /models/
│   ├── speech_recognition.py # Speech-to-text conversion
│   ├── intent_recognition.py # Banking intent detection
│   └── voice_biometrics.py   # Voice authentication logic
├── /services/
│   ├── banking_service.py  # Banking operations
│   └── user_service.py     # User management
├── /static/
│   ├── /css/
│   │   └── style.css       # Frontend styling
│   └── /js/
│       └── app.js          # Frontend logic
├── /templates/
│   └── index.html          # Main application page
└── /uploads/
    └── /audio/             # Temporary storage for audio files
```

## Technical Implementation

### Speech Recognition

- For English and well-supported languages, we use Google's Speech Recognition API
- For low-resource languages like Hindi and Tamil, we employ fine-tuned versions of Wav2Vec2 models

### Intent Recognition

Intent recognition uses a combination of:
- Regular expression pattern matching based on language-specific patterns
- Simple NLP processing using spaCy to handle variations

### Voice Biometrics

The voice authentication system:
- Extracts MFCC features from audio samples
- Uses Gaussian Mixture Models (GMMs) to create voice prints
- Computes likelihood scores for authentication decisions

### Banking Simulation

The banking functionality:
- Uses a simple JSON file as a mock database
- Supports account balance queries
- Processes simulated money transfers
- Returns transaction history

## Limitations and Future Work

This project is a proof-of-concept with the following limitations:

1. **Speech Recognition**: Uses pre-trained models rather than custom-trained LAMs for low-resource languages
2. **Voice Authentication**: Uses basic GMM modeling rather than more sophisticated deep learning approaches
3. **Banking Integration**: Simulates banking operations rather than connecting to actual banking systems
4. **Security**: Implements basic security measures; a production system would need more robust security
5. **Offline Support**: Currently requires internet for some speech recognition; a full implementation would support offline operation

Future work would focus on:
- Training custom LAMs for targeted low-resource languages
- Improving voice biometrics with anti-spoofing measures
- Adding more banking operations
- Creating native mobile applications
- Supporting offline operation for areas with limited connectivity

## License

[Specify license information]

## Contact

[Your contact information]
