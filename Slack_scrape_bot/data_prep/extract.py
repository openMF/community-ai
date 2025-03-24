import json
import datetime
from html import unescape
import sys

def extract_text_from_rich_text_elements(elements):
    """Extract text from rich_text_section elements recursively"""
    text = ""
    if not elements:
        return text
    
    for element in elements:
        if element.get("type") == "text":
            text += element.get("text", "")
        elif element.get("type") == "emoji":
            text += f":{element.get('name', '')}:"
        elif element.get("type") == "link":
            link_text = element.get("text", "")
            url = element.get("url", "")
            if link_text:
                text += f"{link_text} ({url})"
            else:
                text += url
        elif element.get("type") == "user":
            text += f"@user_{element.get('user_id', '')}"
        elif element.get("type") == "usergroup":
            text += f"@usergroup_{element.get('usergroup_id', '')}"
        elif element.get("type") == "rich_text_section":
            text += extract_text_from_rich_text_elements(element.get("elements", []))
    
    return text

def extract_message_content(message):
    """Extract readable content from a message"""
    # Skip join channel messages
    if message.get("subtype") == "channel_join":
        return None
    
    ts = float(message.get("ts", 0))
    date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    
    user = message.get("user", "unknown")
    
    content = message.get("text", "")
    
    if message.get("blocks"):
        for block in message.get("blocks", []):
            if block.get("type") == "rich_text":
                for element in block.get("elements", []):
                    if element.get("type") == "rich_text_section":
                        rich_text = extract_text_from_rich_text_elements(element.get("elements", []))
                        if rich_text and not content:
                            content = rich_text
    
    content = unescape(content)
    
    if not content:
        return None
        
    return f"[{date}] User: {user}\n{content}\n\n"

def process_slack_data(json_data):
    messages = []
    
    if isinstance(json_data, list):
        for item in json_data:
            if isinstance(item, dict) and "m" in item:
                for message in item.get("m", []):
                    content = extract_message_content(message)
                    if content:
                        messages.append(content)
    else:
        if isinstance(json_data, dict) and "m" in json_data:
            for message in json_data.get("m", []):
                content = extract_message_content(message)
                if content:
                    messages.append(content)
    
    return messages

def process_file(input_file, output_file):
    """Process a JSON file and extract messages to an output file"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        messages = process_slack_data(json_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("SLACK CONVERSATION MESSAGES\n")
            f.write("==========================\n\n")
            for message in messages:
                f.write(message)
        
        print(f"Successfully processed {len(messages)} messages from {input_file} to {output_file}")
        
        if messages:
            print("\nPreview of the first message:")
            print(messages[0])
            
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except json.JSONDecodeError:
        print(f"Error: File '{input_file}' is not valid JSON.")
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        process_file(input_file, output_file)
    elif len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = "slack_messages.txt"
        process_file(input_file, output_file)
    else:
        input_file = input("Enter the path to the JSON file: ")
        output_file = input("Enter the path for the output file (or press Enter for 'slack_messages.txt'): ")
        
        if not output_file:
            output_file = "slack_messages.txt"
            
        process_file(input_file, output_file)
