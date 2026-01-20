import pytest
import re
from unittest.mock import MagicMock, patch
# We need to handle the import carefully in case dependencies aren't installed
try:
    from Slack_scraper_bot.scripts.pii_remocval import remove_user_tags, remove_name_lines, clean_text
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from Slack_scraper_bot.scripts.pii_remocval import remove_user_tags, remove_name_lines, clean_text
def test_remove_user_tags(): 
    """Test that Slack user IDs are stripped from timestamps."""
    input_text = "[2024-01-20 12:34:56] User: U123ABCDE Hello world"
    expected = "[2024-01-20 12:34:56] Hello world"
    assert remove_user_tags(input_text).strip() == expected.strip()

def test_remove_name_lines(): 
    """Test that lines identifying names are removed."""
    input_text = "Hello\nmy name is John Doe\nHow are you?"
    # Assuming the script removes the whole line
    result = remove_name_lines(input_text)
    assert "John Doe" not in result
    assert "How are you?" in result

@patch('Slack_scraper_bot.scripts.pii_remocval.create_scrubber')
def test_clean_text_mocked(mock_create_scrubber):
    """Test clean_text by mocking the heavy scrubadub engine."""
    # Setup the mock scrubber
    mock_scrubber = MagicMock()
    mock_scrubber.clean.return_value = "I live in {{LOCATION}}"
    mock_create_scrubber.return_value = mock_scrubber

    result = clean_text("I live in New York")
    assert result == "I live in {{LOCATION}}"
    mock_scrubber.clean.assert_called_once()
