import os

from pydantic import SecretStr
from langchain_groq import ChatGroq
from langchain_core.language_models import BaseChatModel


def get_llm() -> BaseChatModel:

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing required environment variable: GROQ_API_KEY"
        )

    model_id = os.getenv("MODEL", "llama-3.1-8b-instant").strip()
    if not model_id:
        raise ValueError("Model ID cannot be empty.")

    return ChatGroq(
        model=model_id,
        api_key=SecretStr(api_key),
    )
