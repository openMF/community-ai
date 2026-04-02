import os
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr


def get_llm() -> BaseChatModel:

    api_key = os.getenv("LIGHTNING_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing required environment variable: LIGHTNING_API_KEY"
        )

    base_url = os.getenv("LIGHTNING_BASE_URL")
    if not base_url:
        raise ValueError(
            "Missing required environment variable: LIGHTNING_BASE_URL"
        )

    model_id = os.getenv(
        "MODEL", "meta-llama/Llama-3.3-70B-Instruct"
    ).strip()
    if not model_id:
        raise ValueError("Model ID cannot be empty.")

    return ChatOpenAI(
        api_key=SecretStr(api_key),
        base_url=base_url,
        model=model_id
    )
