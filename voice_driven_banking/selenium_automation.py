import os
import time
import zipfile
import json
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class VoiceBankingAutomation:
    def __init__(self, download_dir=None):
        # Set up download directory
        self.download_dir = os.path.abspath(download_dir or "downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # Set up Chrome options
        self.chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        self.chrome_options.add_experimental_option("prefs", prefs)
        self.driver = None
        
        # Define test voice commands and their expected results
        self.test_commands = {
            "balance_inquiry": {
                "command": "What is my account balance",
                "locators": {
                    "input_field": "//input[@id='voice-command-input']",
                    "submit_button": "//button[@id='voice-submit']",
                    "result_container": "//div[contains(@class, 'balance-display')]"
                },
                "success_indicators": ["current balance", "available balance", "$"]
            },
            "fund_transfer": {
                "command": "Transfer $50 to John Doe",
                "locators": {
                    "input_field": "//input[@id='voice-command-input']",
                    "submit_button": "//button[@id='voice-submit']",
                    "result_container": "//div[contains(@class, 'transfer-result')]"
                },
                "success_indicators": ["transfer successful", "transaction completed", "confirmation"]
            },
            "transaction_history": {
                "command": "Show my recent transactions",
                "locators": {
                    "input_field": "//input[@id='voice-command-input']",
                    "submit_button": "//button[@id='voice-submit']",
                    "result_container": "//div[contains(@class, 'transaction-list')]"
                },
                "success_indicators": ["transaction", "date", "amount"]
            }
        }
        
    def start_driver(self):
        """Initialize and start the Chrome driver"""
        self.driver = webdriver.Chrome(options=self.chrome_options)
        
    def clone_repository(self, repo_url):
        """Clone a GitHub repository by downloading and extracting the ZIP"""
        if not self.driver:
            self.start_driver()
            
        try:
            # Navigate to the GitHub repository page
            self.driver.get(repo_url)
            
            # Wait until the "Code" button is clickable and click it
            wait = WebDriverWait(self.driver, 10)
            code_button = wait.until(EC.element_to_be_clickable((By.XPATH, 
                "//button[@data-variant='primary']//span[contains(@class, 'prc-Button-Label-pTQ')]")))
            code_button.click()
            
            # Click on download ZIP
            download_zip = wait.until(EC.element_to_be_clickable((By.XPATH, 
                "//span[contains(text(), 'Download ZIP')]")))
            download_zip.click()
            
            # Wait for the ZIP file to appear in the download folder
            zip_filename = None
            timeout = 60  # seconds
            start_time = time.time()
            while time.time() - start_time < timeout:
                for filename in os.listdir(self.download_dir):
                    if filename.endswith(".zip"):
                        zip_filename = filename
                        break
                if zip_filename:
                    break
                time.sleep(1)
            
            if not zip_filename:
                print("Download timed out or ZIP file not found.")
                return None
                
            zip_path = os.path.join(self.download_dir, zip_filename)
            print(f"Downloaded file: {zip_path}")
            
            # Unzip the downloaded archive into a subfolder called "extracted"
            extract_dir = os.path.join(self.download_dir, "extracted")
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"Extracted ZIP contents to: {extract_dir}")
            
            return extract_dir
            
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return None
    
    def navigate_to_banking_interface(self, url):
        """Navigate to the specified banking interface URL"""
        if not self.driver:
            self.start_driver()
        
        try:
            self.driver.get(url)
            print(f"Navigated to banking interface: {url}")
            return True
        except Exception as e:
            print(f"Error navigating to banking interface: {e}")
            return False
    
    def login(self, username, password):
        """Log in to the banking interface"""
        try:
            # Wait for the username field to be visible and enter username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "username")))
            username_field.clear()
            username_field.send_keys(username)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard')]")))
            
            print("Successfully logged in")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Login failed: {e}")
            return False
    
    def execute_voice_command(self, command_type):
        """Execute a specific voice command and validate the result"""
        if command_type not in self.test_commands:
            print(f"Unknown command type: {command_type}")
            return False
        
        command_data = self.test_commands[command_type]
        
        try:
            # Find and fill the voice command input field
            input_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, command_data["locators"]["input_field"])))
            input_field.clear()
            input_field.send_keys(command_data["command"])
            
            # Click the submit button
            submit_button = self.driver.find_element(By.XPATH, command_data["locators"]["submit_button"])
            submit_button.click()
            
            # Wait for the result container to appear
            result_container = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, command_data["locators"]["result_container"])))
            
            # Validate the result contains expected success indicators
            result_text = result_container.text.lower()
            success = any(indicator.lower() in result_text for indicator in command_data["success_indicators"])
            
            if success:
                print(f"Voice command '{command_type}' executed successfully")
                return True
            else:
                print(f"Voice command '{command_type}' failed validation")
                return False
                
        except Exception as e:
            print(f"Error executing voice command: {e}")
            return False
    
    def run_test_suite(self, banking_url, username, password):
        """Run a full test suite of voice commands"""
        results = {}
        
        # Navigate to the banking interface and login
        if not self.navigate_to_banking_interface(banking_url):
            return {"error": "Failed to navigate to banking interface"}
        
        if not self.login(username, password):
            return {"error": "Failed to login to banking interface"}
        
        # Execute each voice command test
        for command_type in self.test_commands.keys():
            results[command_type] = self.execute_voice_command(command_type)
            time.sleep(2)  # Brief pause between commands
        
        # Generate summary
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        results["summary"] = {
            "success_count": success_count,
            "total_count": total_count,
            "success_rate": f"{(success_count / total_count) * 100:.2f}%"
        }
        
        return results
    
    def save_test_results(self, results, filename="voice_test_results.json"):
        """Save test results to a JSON file"""
        output_path = os.path.join(self.download_dir, filename)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Test results saved to {output_path}")
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

def main():
    # Test configuration
    repo_url = "https://github.com/openMF/mifos-gazelle"
    banking_url = "https://demo.mifos.io"  # Replace with actual banking interface URL
    test_username = "mifos"  # Replace with test account username
    test_password = "password"  # Replace with test account password
    
    # Initialize the automation
    automation = VoiceBankingAutomation()
    
    try:
        # Clone repository (optional if you're just testing banking interface)
        # extract_dir = automation.clone_repository(repo_url)
        
        # Run the test suite
        results = automation.run_test_suite(banking_url, test_username, test_password)
        
        # Save test results
        automation.save_test_results(results)
        
        # Print summary
        print("\n=== Test Summary ===")
        print(f"Success Rate: {results['summary']['success_rate']}")
        print(f"Passed: {results['summary']['success_count']}/{results['summary']['total_count']} tests")
        
    finally:
        # Clean up
        automation.close()

if __name__ == "__main__":
    main()