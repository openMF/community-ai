import re
import sys

def create_scrubber():
    import scrubadub
    import scrubadub_spacy
    scrubber = scrubadub.Scrubber()
    spacy_detector = scrubadub_spacy.detectors.SpacyEntityDetector(model='en_core_web_lg')
    scrubber.add_detector(spacy_detector)
    print("Active detectors:", list(scrubber._detectors.keys()))
    return scrubber

def clean_text(text):
    scrubber = create_scrubber()
    return scrubber.clean(text)

def remove_user_tags(text):
    timestamp_user_pattern = r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] User: [A-Z0-9]{9,12}'
    return re.sub(timestamp_user_pattern, lambda m: m.group(0).split('] User:')[0] + ']', text)

def remove_name_lines(text):
    name_pattern = r'^.*(?:my name is|I am|I\'m).*\n'
    return re.sub(name_pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)

def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    text = clean_text(text)
    text = remove_user_tags(text)
    text = remove_name_lines(text)
    
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(text)
    
    print(f"Cleaned text saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        process_file(input_file, output_file)
    elif len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = "cleaned_slack_messages.txt"
        process_file(input_file, output_file)
    else:
        input_file = input("Enter the path to the txts file: ")
        output_file = input("Enter the path for the output file (or press Enter for 'cleaned_slack_messages.txt'): ")
        
        if not output_file:
            output_file = "cleaned_slack_messages.txt"
            
        process_file(input_file, output_file)