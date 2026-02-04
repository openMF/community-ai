import logging
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, ValidationError
from jira import JIRA
from openai import OpenAI
from github import Github, Auth

# Setup basic logging for config errors
logger = logging.getLogger("mifos-config")


class Settings(BaseSettings):
    """
    Central configuration for the Mifos Community AI Agent.
    Validates environment variables on startup.
    """

    # --- General ---
    APP_ENV: str = Field(default="development", description="Environment: development, production, testing")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # --- OpenAI (Required for Intelligence) ---
    OPENAI_API_KEY: SecretStr = Field(..., description="OpenAI API Key for LLM operations")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Model version to use")

    # --- Jira (Required for Jira Agent) ---
    JIRA_URL: str = Field(..., description="Base URL for the Jira instance")
    JIRA_USERNAME: str = Field(..., description="Email address for Jira login")
    JIRA_API_TOKEN: SecretStr = Field(..., description="Atlassian API Token")

    # --- GitHub (Required for GitHub Agent) ---
    GITHUB_TOKEN: SecretStr = Field(..., description="GitHub Personal Access Token")
    GITHUB_REPOSITORY: str = Field(..., description="Default repository (e.g., 'openMF/community-ai')")

    # --- Slack (Required for Slack Agent) ---
    SLACK_BOT_TOKEN: SecretStr = Field(..., description="Slack Bot User OAuth Token")
    SLACK_APP_TOKEN: Optional[SecretStr] = Field(default=None, description="Slack App-Level Token")

    # --- Fineract / Mifos Sandbox (Required for Banking Agent) ---
    FINERACT_BASE_URL: str = Field(
        default="https://sandbox.mifos.community/fineract-provider/api/v1",
        description="Base URL for Fineract API"
    )
    FINERACT_TENANT_ID: str = Field(default="default", description="Fineract Tenant Identifier")
    FINERACT_USERNAME: str = Field(default="mifos", description="Fineract Login Username")
    FINERACT_PASSWORD: str = Field(default="password", description="Fineract Login Password")

    # --- RAG / Vector DB ---
    VECTOR_DB_PATH: str = Field(default="./data/chroma_db", description="Path to local vector database")

    # Configuration for Pydantic to read from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra keys in .env
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached instance of Settings.
    This prevents reading the .env file on every function call.
    """
    try:
        return Settings()
    except ValidationError as e:
        logger.critical(f"❌ Configuration Error: {e}")
        raise RuntimeError("Application failed to start due to missing or invalid environment variables.") from e


# --- Client Initialization Helpers ---

def get_jira_client() -> JIRA:
    """Initialize Jira client using secure settings."""
    settings = get_settings()
    return JIRA(
        server=settings.JIRA_URL,
        basic_auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN.get_secret_value())
    )


def get_openai_client() -> OpenAI:
    """Initialize OpenAI client."""
    settings = get_settings()
    return OpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())


def get_github_client() -> Github:
    """Initialize PyGithub client."""
    settings = get_settings()
    auth = Auth.Token(settings.GITHUB_TOKEN.get_secret_value())
    return Github(auth=auth)


# Example usage for testing
if __name__ == "__main__":
    try:
        cfg = get_settings()
        print(f"✅ Configuration loaded successfully for: {cfg.APP_ENV}")
        print(f"✅ Jira Target: {cfg.JIRA_URL}")
        print(f"✅ GitHub Repo: {cfg.GITHUB_REPOSITORY}")
        print(f"✅ Fineract Sandbox: {cfg.FINERACT_BASE_URL}")
        print("🚀 All services configured and ready.")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")


        #phase 3 testing