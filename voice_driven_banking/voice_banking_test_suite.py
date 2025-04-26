import os
import json
import time
from voice_simulator import VoiceCommandSimulator
from selenium_automation import VoiceBankingAutomation

class VoiceBankingTestSuite:
    """
    Integrates the voice simulator with the Selenium automation to create
    a complete test suite for voice-driven banking applications.
    """
    
    def __init__(self, config_file=None):
        # Load configuration from file or use defaults
        self.config = self._load_config(config_file)
        
        # Initialize the voice simulator
        self.voice_simulator = VoiceCommandSimulator(
            language=self.config.get("language", "en-US"),
            confidence_range=tuple(self.config.get("confidence_range", (0.85, 0.98)))
        )
        
        # Initialize the Selenium automation
        self.automation = VoiceBankingAutomation(
            download_dir=self.config.get("download_dir", "test_results")
        )
        
        # Initialize test results storage
        self.results = {
            "test_run_id": int(time.time()),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.config,
            "tests": []
        }
    
    def _load_config(self, config_file):
        """Load configuration from a JSON file or return defaults"""
        default_config = {
            "banking_url": "https://demo.mifos.io",
            "username": "mifos",
            "password": "password",
            "language": "en-US",
            "confidence_range": [0.85, 0.98],
            "download_dir": "test_results",
            "commands": [
                {
                    "name": "balance_inquiry",
                    "voice_command": "What is my account balance",
                    "variations": [
                        "Check my balance",
                        "Show me my current balance",
                        "How much money do I have"
                    ]
                },
                {
                    "name": "fund_transfer",
                    "voice_command": "Transfer 50 dollars to John Doe",
                    "variations": [
                        "Send 50 dollars to John",
                        "Pay John Doe 50 dollars",
                        "Move 50 dollars to John's account"
                    ]
                },
                {
                    "name": "transaction_history",
                    "voice_command": "Show my recent transactions",
                    "variations": [
                        "List my recent transactions",
                        "Show transaction history",
                        "What are my recent transactions"
                    ]
                }
            ]
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge user config with defaults
                for key, value in user_config.items():
                    default_config[key] = value
            except Exception as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration")
        
        return default_config
    
    def run_tests(self):
        """Run the complete test suite"""
        try:
            # Start the browser and navigate to the banking interface
            self.automation.start_driver()
            
            # Navigate to banking website
            if not self.automation.navigate_to_banking_interface(self.config["banking_url"]):
                raise Exception("Failed to navigate to banking interface")
            
            # Login
            if not self.automation.login(self.config["username"], self.config["password"]):
                raise Exception("Failed to login to banking interface")
            
            # Run tests for each command
            for command_config in self.config["commands"]:
                command_name = command_config["name"]
                print(f"\nTesting command: {command_name}")
                
                # Test the primary command
                self._test_command(command_name, command_config["voice_command"])
                
                # Test variations if enabled
                if self.config.get("test_variations", True) and "variations" in command_config:
                    for i, variation in enumerate(command_config["variations"]):
                        print(f"Testing variation {i+1}")
                        self._test_command(f"{command_name}_variation_{i+1}", variation)
            
            # Save the results
            self._save_results()
            
            return self.results
            
        except Exception as e:
            print(f"Error running tests: {e}")
            self.results["error"] = str(e)
            self._save_results()
            return self.results
            
        finally:
            # Clean up
            self.automation.close()
    
    def _test_command(self, command_name, command_text):
        """Test a single voice command and record results"""
        # Simulate voice command
        print(f"Simulating voice command: '{command_text}'")
        voice_result = self.voice_simulator.simulate_command(command_text)
        
        # Extract the recognized text
        recognized_text = voice_result["results"][0]["alternatives"][0]["transcript"]
        
        # Find the matching command type
        command_type = None
        for cmd_config in self.config["commands"]:
            if command_name.startswith(cmd_config["name"]):
                command_type = cmd_config["name"]
                break
        
        if not command_type:
            print(f"Warning: Could not identify command type for '{command_name}'")
            command_type = "unknown"
        
        # Execute the command in the banking interface
        result = self.automation.execute_voice_command(command_type)
        
        # Record the test result
        test_result = {
            "command_name": command_name,
            "original_command": command_text,
            "recognized_command": recognized_text,
            "confidence": voice_result["results"][0]["alternatives"][0]["confidence"],
            "success": result,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.results["tests"].append(test_result)
        
        # Print result
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - Original: '{command_text}', Recognized: '{recognized_text}'")
        
        return result
    
    def _save_results(self):
        """Save test results to a JSON file"""
        # Calculate summary statistics
        total_tests = len(self.results["tests"])
        successful_tests = sum(1 for test in self.results["tests"] if test["success"])
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": f"{(successful_tests / total_tests) * 100:.2f}%" if total_tests > 0 else "0%"
        }
        
        # Create output directory if it doesn't exist
        output_dir = self.config.get("download_dir", "test_results")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save to file
        output_path = os.path.join(output_dir, f"voice_test_results_{self.results['test_run_id']}.json")
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=4)
        
        print(f"\nTest results saved to: {output_path}")
        
        # Generate summary report
        print("\n==== Test Summary ====")
        print(f"Total Tests: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Success Rate: {self.results['summary']['success_rate']}")

def main():
    # Run the test suite
    test_suite = VoiceBankingTestSuite()
    test_suite.run_tests()

if __name__ == "__main__":
    main()