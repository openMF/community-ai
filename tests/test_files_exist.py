import os

def test_core_files_exist():
    assert os.path.isfile('README.md'), 'README.md must exist'
    assert os.path.isfile('CodeCommentingScript.py'), 'CodeCommentingScript.py must exist'
