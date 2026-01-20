import pytest
from unittest.mock import patch, MagicMock

# It's important to get the path right for the import
try:
    from Slack_scraper_bot.scripts.summarizer import summarize
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from Slack_scraper_bot.scripts.summarizer import summarize

@patch('Slack_scraper_bot.scripts.summarizer.make_api_call')
def test_summarize_mocked_api_call(mock_make_api_call):
    """
    Test that the summarize function calls the API with the correct prompt
    and returns the mocked summary.
    """
    # Arrange:
    # 1. Configure the mock to return a fake summary
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a mock summary."
    
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    
    mock_make_api_call.return_value = mock_completion
    
    # 2. Define the input text
    input_text = "This is the source code to be summarized."

    # Act:
    # Call the function under test
    result = summarize(input_text)

    # Assert:
    # 1. Check that the function returned the mocked summary
    assert result == "This is a mock summary."

    # 2. Verify that the API call was made once
    mock_make_api_call.assert_called_once()
    
    # 3. Check the content of the prompt sent to the API
    args, kwargs = mock_make_api_call.call_args
    sent_messages = args[1]
    
    assert len(sent_messages) == 2
    assert sent_messages[0]['role'] == 'system'
    assert "Summarize Code-related Files" in sent_messages[0]['content']
    assert sent_messages[1]['role'] == 'user'
    assert sent_messages[1]['content'] == input_text
