import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-2.0-flash")

supported_languages = [
"Arabic","Bengali","Bulgarian","Chinese (Simplified)",
"Chinese (Traditional)","Croatian","Czech","Danish",
"Dutch","English","Estonian","Finnish","French",
"German","Greek","Hebrew","Hindi","Hungarian",
"Indonesian","Italian","Japanese","Korean","Latvian",
"Lithuanian","Norwegian","Polish","Portuguese",
"Romanian","Russian","Serbian","Slovak","Slovenian",
"Spanish","Swahili","Swedish","Thai","Turkish",
"Ukrainian","Vietnamese"
]

def translate_text(input_text, target_language, formal):

    if not input_text:
        return "⚠️ Please enter text to translate."

    tone = "formal" if formal else "informal"

    prompt = f"""
Translate the following text into {target_language} in a {tone} tone.
Return only translated text.

Text:
{input_text}
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"❌ Error: {str(e)}"