# Voice Banking with Document Processing

This extension adds document processing capabilities to the voice-driven banking system, allowing users to perform banking operations using voice commands combined with document scanning.

## Features

- **Document Scanning Integration**: Scan and process different types of documents such as ID cards, bank statements, and payment slips
- **OCR Processing**: Extract text and relevant information from documents using computer vision
- **Voice Command Processing**: Natural language understanding for document-related banking commands
- **Transaction Workflow**: Complete end-to-end workflows like "Transfer money using this payment slip"
- **Identity Verification**: Verify user identity by scanning ID cards
- **Account Verification**: Verify account details by scanning bank statements

## System Architecture

The system consists of the following components:

### 1. Document Processor Module
- Handles document scanning and OCR processing
- Extracts structured information from different document types
- Validates and formats extracted data

### 2. Camera Module
- Manages camera integration for document capture
- Provides visual guidelines to help users position documents
- Captures high-quality images for processing

### 3. Voice-Document Integration
- Bridges the gap between voice commands and document processing
- Manages transaction context across multiple interactions
- Handles multi-step workflows

### 4. Command Processor
- Recognizes document-related commands from voice input
- Routes commands to appropriate handlers
- Manages clarification requests when needed

### 5. Enhanced Voice Banking System
- Integrates document capabilities with the existing voice banking system
- Provides a unified interface for all banking operations
- Handles authentication and session management

## Supported Document Types

1. **ID Cards**
   - Extracts name, ID number, and expiry date
   - Used for identity verification

2. **Payment Slips**
   - Extracts payment amount, payee, and reference number
   - Used for initiating transfers

3. **Bank Statements**
   - Extracts account number, balance, and statement date
   - Used for account verification

## Voice Command Examples

Here are some examples of supported document-related voice commands:

| Command | Description |
|---------|-------------|
| "Scan my ID card" | Scans an ID card and extracts information |
| "Verify my identity using my ID" | Verifies user identity using an ID card |
| "Transfer money using this payment slip" | Initiates a transfer based on a scanned payment slip |
| "Pay this bill" | Processes a bill payment from a scanned document |
| "Scan my bank statement" | Scans a bank statement and extracts account information |
| "Verify my account using this statement" | Verifies account details using a bank statement |

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/voice-banking-docs.git
   cd voice-banking-docs
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Tesseract OCR:
   - For Windows: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - For Linux: `sudo apt-get install tesseract-ocr`
   - For macOS: `brew install tesseract`

## Configuration

Adjust the paths and settings according to your environment.

## Usage

### Running the Application

```
python voice_banking_with_documents.py --config config.json
```

### Basic Workflow

1. The system will start and navigate to the banking interface
2. Log in using the configured credentials
3. You can start issuing voice commands including document-related commands
4. For document scanning, hold the document in front of the camera when prompted
5. The system will extract information from the document and proceed with the requested operation
6. Confirm or reject transactions when prompted

### Example Document Workflow

Here's an example of transferring money using a payment slip:

1. User says: "Transfer money using this payment slip"
2. System activates the camera and displays guidelines
3. User holds the payment slip in front of the camera
4. System captures and processes the image
5. System extracts amount, payee, and reference information
6. System displays extracted information and asks for confirmation
7. User says: "Confirm transaction"
8. System completes the transfer and provides confirmation

## Development

### Project Structure

```
voice-banking-docs/
├── camera_module.py               # Camera capture functionality
├── document_processor.py          # Document OCR and information extraction
├── document_voice_integration.py  # Integration between voice and documents
├── document_command_processor.py  # Document command processing
├── voice_banking_with_documents.py # Main application
├── test_document_integration.py   # Unit tests
├── voice_simulator.py             # Voice command simulation
├── selenium_automation.py         # Banking interface automation
├── voice_banking_test_suite.py    # Test suite
├── config.json                    # Configuration
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

### Adding New Document Types

To add support for a new document type:

1. Add patterns to the `document_patterns` dictionary in `document_processor.py`
2. Add document guidelines in `camera_module.py`
3. Create extraction methods in `document_processor.py`
4. Add command patterns in `document_command_processor.py`
5. Implement handling methods in `document_voice_integration.py`

### Running Tests

```
python -m unittest test_document_integration.py
```

## Requirements

- Python 3.7+
- OpenCV 4.5+
- Tesseract OCR 4.0+
- Selenium 4.0+
- Chrome browser and ChromeDriver
- Webcam or camera device

## License

This project is licensed under the MIT License - see the LICENSE file for details.
