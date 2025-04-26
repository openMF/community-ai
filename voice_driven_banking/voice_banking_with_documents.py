import os
import json
import time
import argparse
from selenium_automation import VoiceBankingAutomation
from voice_simulator import VoiceCommandSimulator
from document_command_processor import DocumentCommandProcessor

class EnhancedVoiceBankingSystem:
    """
    Enhanced voice banking system that integrates document scanning capabilities
    with voice commands for a more complete banking experience.
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the enhanced voice banking system.
        
        Args:
            config_file: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize the standard banking automation
        self.banking_automation = VoiceBankingAutomation(
            download_dir=self.config.get("download_dir", "test_results")
        )
        
        # Initialize the voice simulator
        self.voice_simulator = VoiceCommandSimulator(
            language=self.config.get("language", "en-US"),
            confidence_range=tuple(self.config.get("confidence_range", (0.85, 0.98)))
        )
        
        # Initialize the document command processor
        self.doc_processor = DocumentCommandProcessor(config_file)
        
        # Conversation context
        self.context = {
            "session_id": int(time.time()),
            "authenticated": False,
            "last_command": None,
            "pending_clarification": None,
            "transaction_history": []
        }
    
    def _load_config(self, config_file):
        """
        Load configuration from JSON file or use defaults.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        # Try to load from the provided config file
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                print("Using default configuration from voice_driven_banking/config.json")
        
        # Fall back to default config
        default_config_path = "voice_driven_banking/config.json"
        if os.path.exists(default_config_path):
            try:
                with open(default_config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading default config: {e}")
        
        # Use hardcoded defaults if all else fails
        return {
            "banking_url": "https://demo.mifos.io",
            "username": "mifos",
            "password": "password",
            "language": "en-US",
            "confidence_range": [0.85, 0.98],
            "download_dir": "test_results",
            "test_variations": True,
            "record_video": False,
            "commands": [
                {
                    "name": "balance_inquiry",
                    "voice_command": "What is my account balance",
                    "variations": [
                        "Check my balance",
                        "Show me my current balance",
                        "How much money do I have"
                    ],
                    "locators": {
                        "input_field": "//input[@id='voice-command-input']",
                        "submit_button": "//button[@id='voice-submit']",
                        "result_container": "//div[contains(@class, 'balance-display')]"
                    },
                    "success_indicators": ["current balance", "available balance", "$"]
                },
                {
                    "name": "fund_transfer",
                    "voice_command": "Transfer 50 dollars to John Doe",
                    "variations": [
                        "Send 50 dollars to John",
                        "Pay John Doe 50 dollars",
                        "Move 50 dollars to John's account"
                    ],
                    "locators": {
                        "input_field": "//input[@id='voice-command-input']",
                        "submit_button": "//button[@id='voice-submit']",
                        "result_container": "//div[contains(@class, 'transfer-result')]"
                    },
                    "success_indicators": ["transfer successful", "transaction completed", "confirmation"]
                },
                {
                    "name": "transaction_history",
                    "voice_command": "Show my recent transactions",
                    "variations": [
                        "List my recent transactions",
                        "Show transaction history",
                        "What are my recent transactions"
                    ],
                    "locators": {
                        "input_field": "//input[@id='voice-command-input']",
                        "submit_button": "//button[@id='voice-submit']",
                        "result_container": "//div[contains(@class, 'transaction-list')]"
                    },
                    "success_indicators": ["transaction", "date", "amount"]
                }
            ]
        }
    
    def start(self):
        """
        Start the banking system and login.
        """
        # Start the Selenium browser
        self.banking_automation.start_driver()
        
        # Navigate to banking website
        if not self.banking_automation.navigate_to_banking_interface(self.config["banking_url"]):
            print("Failed to navigate to banking interface")
            return False
        
        # Login
        if not self.banking_automation.login(self.config["username"], self.config["password"]):
            print("Failed to login to banking interface")
            return False
        
        self.context["authenticated"] = True
        return True
    
    def stop(self):
        """
        Stop the banking system.
        """
        self.banking_automation.close()
        
        # Make sure camera is stopped if it was started
        try:
            self.doc_processor.doc_integration.stop_camera()
        except:
            pass
    
    def process_voice_command(self, command_text=None):
        """
        Process a voice command, either provided as text or simulated.
        
        Args:
            command_text: Text of the command (if None, will use voice simulator)
            
        Returns:
            Result of the command
        """
        # If no command text provided, simulate a voice command
        if command_text is None:
            print("Please speak a command...")
            # In a real system, this would use an actual speech recognition API
            command_text = input("Enter command (simulating speech): ")
        
        # Simulate voice recognition
        recognition_result = self.voice_simulator.simulate_command(command_text)
        recognized_text = recognition_result['results'][0]['alternatives'][0]['transcript']
        confidence = recognition_result['results'][0]['alternatives'][0]['confidence']
        
        print(f"Recognized: '{recognized_text}' (confidence: {confidence:.2f})")
        
        # Store the command in context
        self.context["last_command"] = {
            "original": command_text,
            "recognized": recognized_text,
            "confidence": confidence,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Check if we're waiting for clarification
        if self.context.get("pending_clarification"):
            return self._handle_clarification(recognized_text)
        
        # First, check if it's a document-related command
        doc_result = self.doc_processor.process_command(recognized_text)
        
        if doc_result:
            # It's a document command
            print(f"Document command detected: {doc_result.get('intent', 'unknown')}")
            
            # Check if clarification is needed
            if doc_result.get("status") == "clarification_needed":
                self.context["pending_clarification"] = {
                    "type": doc_result.get("clarification_type"),
                    "original_command": recognized_text
                }
                return {
                    "status": "clarification_requested",
                    "message": doc_result.get("message", "Please clarify your request."),
                    "original_command": recognized_text
                }
            
            # Add to transaction history if it's a completed transaction
            if doc_result.get("status") in ["completed", "transaction_completed"]:
                self.context["transaction_history"].append({
                    "type": "document_transaction",
                    "details": doc_result.get("details", {}),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return doc_result
        else:
            # It's a standard banking command
            print(f"Standard banking command detected: '{recognized_text}'")
            
            # Find matching command type
            command_type = self._identify_command_type(recognized_text)
            
            if command_type:
                # Execute the command
                result = self.banking_automation.execute_voice_command(command_type)
                
                # Create a structured result
                command_result = {
                    "status": "completed" if result else "failed",
                    "command_type": command_type,
                    "original_command": recognized_text,
                    "success": result
                }
                
                return command_result
            else:
                return {
                    "status": "unknown_command",
                    "message": "Sorry, I didn't understand that command.",
                    "original_command": recognized_text
                }
    
    def _handle_clarification(self, response):
        """
        Handle user response to a clarification request.
        
        Args:
            response: User's response to the clarification
            
        Returns:
            Result after clarification
        """
        clarification_info = self.context["pending_clarification"]
        clarification_type = clarification_info.get("type")
        
        # Clear the pending clarification
        self.context["pending_clarification"] = None
        
        # Process the clarification
        result = self.doc_processor.handle_clarification_response(clarification_type, response)
        
        # Add original command context
        result["original_command"] = clarification_info.get("original_command")
        result["clarification_response"] = response
        
        return result
    
    def _identify_command_type(self, command_text):
        """
        Identify the type of standard banking command.
        
        Args:
            command_text: Recognized command text
            
        Returns:
            Command type if identified, None otherwise
        """
        command_text = command_text.lower()
        
        # Check against each command type in the config
        for command in self.config.get("commands", []):
            # Check the main command
            if command["voice_command"].lower() in command_text:
                return command["name"]
            
            # Check variations
            for variation in command.get("variations", []):
                if variation.lower() in command_text:
                    return command["name"]
        
        return None
    
    def get_available_commands(self):
        """
        Get a list of all available commands.
        
        Returns:
            Dictionary with standard and document commands
        """
        # Get standard commands
        standard_commands = []
        for cmd in self.config.get("commands", []):
            standard_commands.append({
                "name": cmd["name"],
                "example": cmd["voice_command"],
                "variations": cmd.get("variations", [])
            })
        
        # Get document commands
        doc_commands = self.doc_processor.get_document_commands_help()
        
        return {
            "standard_commands": standard_commands,
            "document_commands": doc_commands
        }
    
    def get_transaction_history(self):
        """
        Get the transaction history for the current session.
        
        Returns:
            List of transactions in the current session
        """
        return self.context.get("transaction_history", [])
    
    def run_interactive_session(self):
        """
        Run an interactive voice banking session.
        """
        print("\n===== Enhanced Voice Banking System with Document Processing =====")
        print("Say 'exit' or 'quit' to end the session\n")
        
        try:
            if not self.start():
                print("Failed to start banking session.")
                return
            
            # Show available commands
            commands = self.get_available_commands()
            print("\nAvailable standard commands:")
            for cmd in commands["standard_commands"]:
                print(f"- {cmd['example']}")
            
            print("\nAvailable document commands:")
            for cmd in commands["document_commands"]["commands"]:
                print(f"- {cmd['examples'][0]} ({cmd['description']})")
            
            print("\nStarting voice recognition...\n")
            
            while True:
                command = input("Enter voice command (or 'exit'): ")
                
                if command.lower() in ["exit", "quit", "stop"]:
                    break
                
                result = self.process_voice_command(command)
                
                # Display the result
                if result.get("status") == "completed":
                    print(f" Command successful: {result.get('message', 'Command executed successfully')}")
                elif result.get("status") == "clarification_requested":
                    print(f" {result.get('message')}")
                elif result.get("status") == "ready_for_transfer":
                    print(f" {result.get('message')} - Say 'confirm transaction' to proceed")
                elif result.get("status") == "document_scanned":
                    print(f" Document scanned: {result.get('document_type')}")
                    details = result.get("details", {})
                    for key, value in details.items():
                        if key != "raw_text" and key != "confidence":
                            print(f"   - {key}: {value}")
                elif result.get("status") == "identity_verified":
                    print(f" {result.get('message')}")
                elif result.get("status") == "account_verified":
                    print(f" {result.get('message')}")
                    if "details" in result:
                        print(f"   - Account: {result['details'].get('account_number', 'Unknown')}")
                        print(f"   - Balance: {result['details'].get('balance', 'Unknown')}")
                elif result.get("status") == "low_confidence":
                    print(f" {result.get('message')}")
                elif result.get("status") == "error":
                    print(f" Error: {result.get('message', 'Unknown error')}")
                else:
                    print(f"Result: {result}")
                
                print()
        
        finally:
            self.stop()
            print("\nBanking session ended.")


def main():
    """
    Main entry point for the enhanced voice banking system.
    """
    parser = argparse.ArgumentParser(description="Enhanced Voice Banking System with Document Processing")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Create and run the enhanced banking system
    banking_system = EnhancedVoiceBankingSystem(args.config)
    banking_system.run_interactive_session()


if __name__ == "__main__":
    main()