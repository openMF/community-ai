# Voice-Driven Banking via LAMs: Demonstration Guide

This guide provides a step-by-step demonstration of the Voice-Driven Banking proof-of-concept, showcasing its multilingual capabilities, voice recognition features, and banking functionalities.

## Table of Contents
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [User Authentication](#user-authentication)
- [Voice Banking Demo](#voice-banking-demo)
- [Multilingual Support](#multilingual-support)
- [Voice Biometrics](#voice-biometrics)
- [Troubleshooting](#troubleshooting)

## Setup

### Prerequisites
- Python 3.9 or higher
- Miniconda or Anaconda (recommended)
- Modern web browser with microphone access
- Internet connection

### Installation

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd GSoC'25 Mifos POC
   ```

2. **Set up the environment** (choose one method):

   **Using Conda** (recommended):
   ```
   conda env create -f environment.yml
   conda activate voice-banking
   ```

   **Using pip**:
   ```
   pip install -r requirements.txt
   ```

3. **Download language models**:
   ```
   python -m spacy download en_core_web_sm
   python -m spacy download xx_ent_wiki_sm
   ```

## Running the Application

1. **Start the server**:

   On Windows:
   ```
   run.bat
   ```

   On macOS/Linux:
   ```
   chmod +x run.sh
   ./run.sh
   ```

   Or manually:
   ```
   python app.py
   ```

2. **Access the web interface** by opening a browser and navigating to:
   ```
   http://127.0.0.1:5000
   ```

3. **Allow microphone access** when prompted by your browser.

## User Authentication

### Demo Accounts
Use these pre-configured accounts for quick testing:

| Username | Password | Language |
|----------|----------|----------|
| johndoe  | password123 | English (en-US) |
| janesmith | password456 | Hindi (hi-IN) |
| jacobbrown | password789 | Tamil (ta-IN) |

### Login Process
1. On the login screen, enter the username and password
2. Click the "Login" button
3. Upon successful login, you'll be redirected to the banking interface

![Login Screen](images/login_screen.png) *(Screenshot description: Login form with username and password fields)*

### Registration Process
1. Click "Register here" on the login screen
2. Fill in all the required details:
   - Username (unique identifier)
   - Password
   - Full Name
   - Email
   - Phone
   - Preferred Language (English, Hindi, or Tamil)
3. Click "Register" to create your account
4. After successful registration, you'll be redirected to the login page

![Registration Screen](images/registration_screen.png) *(Screenshot description: Registration form with all fields)*

## Voice Banking Demo

### Checking Account Balance

1. **Set up**: Log in to your account and ensure your microphone is working
2. **Select Language**: Choose your preferred language from the dropdown
3. **Start Recording**: Click the "Start Recording" button with the microphone icon
4. **Speak Command**: Say one of the following phrases (based on selected language):
   - English: "What is my account balance?" or "Check my balance"
   - Hindi: "मेरा बैलेंस क्या है" or "मेरा बैलेंस दिखाएं"
   - Tamil: "என் இருப்பு என்ன" or "என் கணக்கு இருப்பு காட்டு"
5. **Wait for Processing**: The system will process your speech (this may take a few seconds)
6. **View Results**: You'll see:
   - Recognized text (what the system heard)
   - Preprocessed text (after normalization)
   - Detected intent (Balance Check)
   - Response with your account balances

![Balance Check Demo](images/balance_check.png) *(Screenshot description: Interface showing recognized speech and account balance information)*

### Transferring Money

1. **Start Recording**: Click the microphone button
2. **Speak Command**: Say something like:
   - English: "Transfer 100 dollars to Jane" or "Send 50 to John"
   - Hindi: "जेन को 100 रुपये ट्रांसफर करें"
   - Tamil: "ஜேனுக்கு 100 ரூபாய் அனுப்பு"
3. **View Results**: The system will display:
   - The recognized command
   - The transfer details (amount and recipient)
   - Confirmation of the transaction
   - Updated account balance

![Money Transfer Demo](images/transfer_demo.png) *(Screenshot description: Interface showing transfer command recognition and confirmation)*

### Viewing Transaction History

1. **Start Recording**: Click the microphone button
2. **Speak Command**: Say something like:
   - English: "Show my recent transactions" or "Show transaction history"
   - Hindi: "मेरे हाल के लेनदेन दिखाएं"
   - Tamil: "என் சமீபத்திய பரிவர்த்தனைகளைக் காட்டு"
3. **View Results**: The system will display:
   - Your recent transactions in a table format
   - Date, type, amount, and description for each transaction

![Transaction History Demo](images/transaction_history.png) *(Screenshot description: Interface showing transaction history table)*

## Multilingual Support

### Changing Languages

1. Select your preferred language from the dropdown menu in the banking interface
2. The example phrases will update to show commands in the selected language
3. Speak in the selected language for optimal recognition

### Language Support Details

| Language | Code | Speech Recognition | Banking Commands |
|----------|------|-------------------|------------------|
| English | en-US | Google Speech API | Full support |
| Hindi | hi-IN | Wav2Vec2 (Harveen Chadha) | Full support |
| Tamil | ta-IN | Wav2Vec2 (Harveen Chadha) | Full support |

### Demonstration Video

![Language Switching](images/language_demo.gif) *(GIF description: Demonstration of switching languages and speaking commands)*

## Voice Biometrics

The POC includes a simplified voice biometrics system for authentication.

### First-time Use

1. On first voice interaction, the system will automatically enroll your voice
2. A voice print is created and stored for future authentication

### Authentication Process

1. For subsequent voice commands, your voice is automatically verified
2. The authentication happens seamlessly before processing your commands
3. If authentication fails, you'll see an error message

> **Note**: For the POC, authentication thresholds are set low to facilitate demonstrations. In a production environment, more strict thresholds would be applied.

## Troubleshooting

### Common Issues and Solutions

#### Microphone Not Working
- Ensure your browser has permission to access the microphone
- Check if your microphone is working in other applications
- Try using a different browser (Chrome recommended)

