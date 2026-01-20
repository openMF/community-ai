import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure the project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import importlib

@patch('selenium.webdriver.Chrome')
def test_clone_repository_mocked(mock_chrome):
    """Verify the browser is initialized without actually opening Chrome."""
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver

    # Use a dummy path and URL
    # We need to mock the rest of the selenium and os calls to avoid errors
    with (patch('selenium.webdriver.support.ui.WebDriverWait') as mock_wait,
          patch('os.listdir', return_value=['dummy.zip']),
          patch('os.path.exists', return_value=True),
          patch('zipfile.ZipFile')):
        
        # Configure the mock for WebDriverWait's .until() method
        mock_wait_instance = mock_wait.return_value
        mock_clickable_element = MagicMock()
        mock_wait_instance.until.return_value = mock_clickable_element
        
        # Import the module here, after patches are active
        repo_cloner_path = "Repo Clone Automation.repo_cloner"
        repo_cloner = importlib.import_module(repo_cloner_path)
        
        repo_cloner.clone_repository("https://github.com/test/repo", "./test_downloads")
    
    # Verify interaction
    mock_driver.get.assert_called_with("https://github.com/test/repo")
    assert mock_clickable_element.click.call_count == 2
    mock_driver.quit.assert_called()
