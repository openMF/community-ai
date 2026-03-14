import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

def get_llm() -> BaseChatModel:

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing required environment variable: GOOGLE_API_KEY"
        )

    model_id = os.getenv("MODEL", "models/gemini-3-pro-preview").strip()
    if not model_id:
        raise ValueError("Model ID cannot be empty.")

    return ChatGoogleGenerativeAI(
        model=model_id,
        api_key=SecretStr(api_key),
        disable_streaming="tool_calling"
    )
