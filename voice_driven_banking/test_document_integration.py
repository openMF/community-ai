import unittest
import os
import sys
import json
import cv2
import numpy as np
from unittest.mock import patch, MagicMock

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_processor import DocumentProcessor
from document_voice_integration import DocumentVoiceIntegration
from document_command_processor import DocumentCommandProcessor

class TestDocumentIntegration(unittest.TestCase):
    """
    Unit tests for the document integration modules.
    """
    
    def setUp(self):
        """
        Set up test environment before each test.
        """
        # Create test directory if it doesn't exist
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files")
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        # Create a test config file
        self.config_path = os.path.join(self.test_dir, "test_config.json")
        test_config = {
            "captured_images_dir": self.test_dir,
            "min_confidence_threshold": 0.5,
            "verification_required": True,
            "default_camera_id": 0,
            "max_amount_without_verification": 100,
            "supported_document_types": ["id_card", "bank_statement", "payment_slip"]
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Create test document images
        self._create_test_images()
    
    def tearDown(self):
        """
        Clean up after each test.
        """
        # Remove test files
        for file in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
    
    def _create_test_images(self):
        """
        Create test document images for testing.
        """
        # Create a simple ID card test image with text
        id_card = np.ones((300, 500, 3), dtype=np.uint8) * 255
        cv2.putText(id_card, "ID CARD", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(id_card, "Name: John Doe", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(id_card, "ID No: ABC123456789", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(id_card, "Expiry: 01/01/2030", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.rectangle(id_card, (20, 20), (480, 280), (0, 0, 0), 2)
        
        # Save the ID card image
        self.id_card_path = os.path.join(self.test_dir, "test_id_card.jpg")
        cv2.imwrite(self.id_card_path, id_card)
        
        # Create a simple payment slip test image
        payment_slip = np.ones((400, 600, 3), dtype=np.uint8) * 255
        cv2.putText(payment_slip, "PAYMENT SLIP", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(payment_slip, "Amount: $150.00", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(payment_slip, "Payee: Jane Smith", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(payment_slip, "Reference: INV2023001", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.rectangle(payment_slip, (20, 20), (580, 380), (0, 0, 0), 2)
        
        # Save the payment slip image
        self.payment_slip_path = os.path.join(self.test_dir, "test_payment_slip.jpg")
        cv2.imwrite(self.payment_slip_path, payment_slip)
        
        # Create a simple bank statement test image
        bank_statement = np.ones((500, 700, 3), dtype=np.uint8) * 255
        cv2.putText(bank_statement, "BANK STATEMENT", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(bank_statement, "Account Number: 12345678901234", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(bank_statement, "Balance: $2,500.75", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(bank_statement, "Date: 15/04/2023", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.rectangle(bank_statement, (20, 20), (680, 480), (0, 0, 0), 2)
        
        # Save the bank statement image
        self.bank_statement_path = os.path.join(self.test_dir, "test_bank_statement.jpg")
        cv2.imwrite(self.bank_statement_path, bank_statement)
    
    @patch('pytesseract.image_to_string')
    def test_document_processor(self, mock_image_to_string):
        """
        Test the DocumentProcessor class.
        """
        # Mock pytesseract.image_to_string response for ID card
        mock_image_to_string.return_value = """
        ID CARD
        Name: John Doe
        ID No: ABC123456789
        Expiry: 01/01/2030
        """
        
        # Initialize DocumentProcessor
        processor = DocumentProcessor()
        
        # Test ID card extraction
        id_result = processor.extract_id_info(self.id_card_path)
        
        # Check results
        self.assertIn("name", id_result)
        self.assertEqual(id_result["name"], "John Doe")
        self.assertIn("id_number", id_result)
        self.assertEqual(id_result["id_number"], "ABC123456789")
        self.assertIn("expiry", id_result)
        
        # Mock pytesseract.image_to_string response for payment slip
        mock_image_to_string.return_value = """
        PAYMENT SLIP
        Amount: $150.00
        Payee: Jane Smith
        Reference: INV2023001
        """
        
        # Test payment slip extraction
        payment_result = processor.extract_payment_details(self.payment_slip_path)
        
        # Check results
        self.assertIn("amount", payment_result)
        self.assertIsInstance(payment_result["amount"], float)
        self.assertAlmostEqual(payment_result["amount"], 150.0, delta=0.1)
        self.assertIn("payee", payment_result)
        self.assertEqual(payment_result["payee"], "Jane Smith")
        self.assertIn("reference", payment_result)
        self.assertEqual(payment_result["reference"], "INV2023001")
        
        # Mock pytesseract.image_to_string response for bank statement
        mock_image_to_string.return_value = """
        BANK STATEMENT
        Account Number: 12345678901234
        Balance: $2,500.75
        Date: 15/04/2023
        """
        
        # Test bank statement extraction
        statement_result = processor.extract_account_info(self.bank_statement_path)
        
        # Check results
        self.assertIn("account_number", statement_result)
        self.assertEqual(statement_result["account_number"], "12345678901234")
        self.assertIn("balance", statement_result)
        self.assertIsInstance(statement_result["balance"], float)
        self.assertAlmostEqual(statement_result["balance"], 2500.75, delta=0.1)
        self.assertIn("date", statement_result)
    
    @patch('document_voice_integration.DocumentVoiceIntegration.start_camera')
    @patch('document_voice_integration.DocumentVoiceIntegration.stop_camera')
    @patch('document_voice_integration.DocumentProcessor')
    def test_document_voice_integration(self, mock_processor, mock_stop_camera, mock_start_camera):
        """
        Test the DocumentVoiceIntegration class.
        """
        # Mock the document processor
        mock_processor_instance = mock_processor.return_value
        mock_processor_instance.extract_payment_details.return_value = {
            "amount": 150.0,
            "payee": "Jane Smith",
            "reference": "INV2023001",
            "confidence": 0.85
        }
        
        # Initialize DocumentVoiceIntegration
        integration = DocumentVoiceIntegration(
            config_path=self.config_path,
            tesseract_path=None,
            camera_id=0
        )
        
        # Replace the doc_processor with the mock
        integration.doc_processor = mock_processor_instance
        
        # Mock the camera capture
        integration.camera = MagicMock()
        integration.camera.capture_document.return_value = (self.payment_slip_path, None)
        
        # Test process_payment_document
        result = integration.process_payment_document()
        
        # Check results
        self.assertEqual(result["status"], "ready_for_transfer")
        self.assertIn("details", result)
        self.assertEqual(result["details"]["amount"], 150.0)
        self.assertEqual(result["details"]["payee"], "Jane Smith")
        
        # Test confirm_transaction
        integration.transaction_context["payment_info"] = {
            "amount": 50.0,
            "payee": "Test Payee",
            "reference": "TEST123"
        }
        
        confirm_result = integration.confirm_transaction(confirmed=True)
        self.assertEqual(confirm_result["status"], "completed")
        
        # Test cancel_transaction
        integration.transaction_context["payment_info"] = {
            "amount": 50.0,
            "payee": "Test Payee",
            "reference": "TEST123"
        }
        
        cancel_result = integration.confirm_transaction(confirmed=False)
        self.assertEqual(cancel_result["status"], "cancelled")
    
    @patch('document_command_processor.DocumentVoiceIntegration')
    def test_document_command_processor(self, mock_integration):
        """
        Test the DocumentCommandProcessor class.
        """
        # Mock the integration module
        mock_integration_instance = mock_integration.return_value
        mock_integration_instance.scan_identity_document.return_value = {
            "status": "document_scanned",
            "message": "ID card scanned successfully",
            "document_type": "id_card",
            "details": {
                "name": "John Doe",
                "id_number": "ABC123456789",
                "expiry": "01/01/2030",
                "confidence": 0.9
            }
        }
        
        # Initialize DocumentCommandProcessor
        processor = DocumentCommandProcessor(self.config_path)
        
        # Replace the doc_integration with the mock
        processor.doc_integration = mock_integration_instance
        
        # Test command identification
        commands = [
            "Scan my ID card please",
            "Verify my identity using my ID",
            "Transfer money using this payment slip",
            "Check my account with this bank statement"
        ]
        
        for command in commands:
            result = processor.process_command(command)
            self.assertIsNotNone(result, f"Failed to recognize command: {command}")
            self.assertIn("intent", result)
            
        # Test specific command handling
        scan_result = processor.process_command("Scan my ID card")
        self.assertEqual(scan_result["intent"], "scan_document")
        mock_integration_instance.scan_identity_document.assert_called_once()


if __name__ == "__main__":
    unittest.main()
