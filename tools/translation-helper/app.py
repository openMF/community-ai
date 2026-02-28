import os
import tempfile
import gradio as gr
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS

# Load API Key from .env
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model_name = "llama-3.3-70b-versatile"  # Latest and recommended versatile model from Groq

# Supported languages (from the list you shared)
supported_languages = [
    "Arabic", "Bengali", "Bulgarian", "Chinese (Simplified)", "Chinese (Traditional)", 
    "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", 
    "French", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Indonesian", 
    "Italian", "Japanese", "Korean", "Latvian", "Lithuanian", "Norwegian", 
    "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Slovak", 
    "Slovenian", "Spanish", "Swahili", "Swedish", "Thai", "Turkish", "Ukrainian", 
    "Vietnamese"
]

# Language codes for gTTS
LANGUAGE_CODES = {
    "Arabic": "ar", "Bengali": "bn", "Bulgarian": "bg", "Chinese (Simplified)": "zh-CN", 
    "Chinese (Traditional)": "zh-TW", "Croatian": "hr", "Czech": "cs", "Danish": "da", 
    "Dutch": "nl", "English": "en", "Estonian": "et", "Finnish": "fi", "French": "fr", 
    "German": "de", "Greek": "el", "Hebrew": "iw", "Hindi": "hi", "Hungarian": "hu", 
    "Indonesian": "id", "Italian": "it", "Japanese": "ja", "Korean": "ko", "Latvian": "lv", 
    "Lithuanian": "lt", "Norwegian": "no", "Polish": "pl", "Portuguese": "pt", 
    "Romanian": "ro", "Russian": "ru", "Serbian": "sr", "Slovak": "sk", "Slovenian": "sl", 
    "Spanish": "es", "Swahili": "sw", "Swedish": "sv", "Thai": "th", "Turkish": "tr", 
    "Ukrainian": "uk", "Vietnamese": "vi"
}

# Translation logic
def translate_text(input_text, target_language, formal):
    if target_language not in supported_languages:
        return "❌ Error: The selected language is not supported.", None
    
    tone = "formal" if formal else "informal"
    prompt = f"Translate the following text into {target_language} in a {tone} tone. Only provide the translated text without any explanation or additional commentary:\n\n{input_text}"
    
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.3,
            stream=False,
        )
        translated_text = completion.choices[0].message.content.strip()
        
        # Generate Audio using gTTS
        lang_code = LANGUAGE_CODES.get(target_language, "en")
        try:
            tts = gTTS(text=translated_text, lang=lang_code)
            # Create a temporary file to store audio
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(temp_audio.name)
            audio_path = temp_audio.name
        except Exception as audio_err:
            print(f"Audio generation failed: {audio_err}")
            audio_path = None
            
        return translated_text, audio_path
        
    except Exception as e:
        return f"❌ Error: {e}", None

# Gradio Interface
with gr.Blocks(title="Translation Helper") as app:
    gr.Markdown("# Translation & Text-to-Speech Tool")
    gr.Markdown("Translate English text to supported languages and generate audio pronunciation.")

    with gr.Row():
        input_text = gr.Textbox(label="English Input", placeholder="Enter text here...", interactive=True)
        language = gr.Dropdown(choices=supported_languages, label="Target Language")
        tone = gr.Checkbox(label="Use Formal Tone", value=True)
    
    translate_btn = gr.Button("Translate")
    output_text = gr.Textbox(label="Translated Text")
    output_audio = gr.Audio(label="Audio Output", type="filepath")

    # Trigger translation when "Enter" is pressed on the input_text textbox
    input_text.submit(fn=translate_text, inputs=[input_text, language, tone], outputs=[output_text, output_audio])

    # Button click still works as fallback
    translate_btn.click(fn=translate_text, inputs=[input_text, language, tone], outputs=[output_text, output_audio])

# Run app
if __name__ == "__main__":
    app.launch()
