def test_readme_contains_headers():
    with open('README.md', 'r', encoding='utf-8') as fh:
        text = fh.read()
    assert '# Mifos Community AI Chatbot' in text
    assert '## Project purpose & scope' in text
    assert '## Quick start (run locally)' in text
