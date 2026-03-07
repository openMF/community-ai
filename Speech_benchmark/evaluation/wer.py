from jiwer import wer

def calculate_wer(reference, hypothesis):

    error = wer(reference, hypothesis)

    return error