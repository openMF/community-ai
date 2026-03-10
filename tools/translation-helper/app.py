import gradio as gr
from translator.translate import translate_text, supported_languages

with gr.Blocks(title="AI Translator") as app:

    gr.Markdown("# 🌐 AI Translator using Gemini 2.0 Flash")

    with gr.Row():
        input_text = gr.Textbox(
            label="Enter Text",
            placeholder="Type text to translate..."
        )

        language = gr.Dropdown(
            choices=supported_languages,
            label="Target Language"
        )

        tone = gr.Checkbox(
            label="Formal Tone",
            value=True
        )

    translate_btn = gr.Button("Translate 🔁")

    output_text = gr.Textbox(
        label="Translated Output"
    )

    translate_btn.click(
        fn=translate_text,
        inputs=[input_text, language, tone],
        outputs=output_text
    )

if __name__ == "__main__":
    app.launch()