import os
import logging
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, ValidationError

# Setup basic logging for config errors
logger = logging.getLogger("mifos-config")

# --- PATH CORRECTION LOGIC ---
# Ensures we find the .env file regardless of where the script is run
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Assumes .env is in the same folder as this config file, or adjust ".." as needed
# If your .env is at the project ROOT, you might need: os.path.join(CURRENT_DIR, "..", "..", ".env")
DOTENV_PATH = os.path.join(CURRENT_DIR, ".env")


class Settings(BaseSettings):
    """
    Central configuration for the Mifos Community AI Agent.
    Validates environment variables on startup.
    """

    # --- General & Watchdog (Phase 5) ---
    APP_ENV: str = Field(
        default="development",
        description="Environment: development, production, testing",
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    WATCHDOG_POLLING_INTERVAL: int = Field(
        default=3600,
        description="Interval in seconds for background checks (default: 1 hour)",
    )
    SLACK_REPORT_CHANNEL_ID: str = Field(
        default="",
        description="Channel ID where the Watchdog posts intelligence reports",
    )
    SLACK_ALERT_CHANNEL_ID: str = Field(
        default="",
        description="Channel ID for instant PR and CI alerts (e.g. #mcp_testing)",
    )

    # --- OpenAI ---
    OPENAI_API_KEY: SecretStr = Field(
        ..., description="OpenAI API Key for LLM operations"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini", description="Model version to use"
    )

    # --- Jira ---
    JIRA_URL: str = Field(..., description="Base URL for the Jira instance")

    # ✅ FIX: Renamed back to JIRA_EMAIL so 'settings.JIRA_EMAIL' works in code
    JIRA_EMAIL: str = Field(
        ...,
        description="Jira username/email"
    )

    JIRA_API_TOKEN: SecretStr = Field(..., description="Atlassian API token")

    # --- GitHub & Webhook Security ---
    GITHUB_TOKEN: SecretStr = Field(
        ..., description="GitHub Personal Access Token"
    )
    GITHUB_REPOSITORY: str = Field(
        ..., description="Target repository (e.g., 'openMF/fineract')"
    )
    GITHUB_WEBHOOK_SECRET: Optional[SecretStr] = Field(
        None, description="Secret used to verify incoming GitHub webhooks"
    )

    # --- Slack ---
    SLACK_BOT_TOKEN: SecretStr = Field(
        ..., description="Slack Bot User OAuth Token"
    )
    SLACK_SIGNING_SECRET: SecretStr = Field(
        ..., description="Slack Signing Secret for request verification"
    )

    # --- RAG / Pinecone Vector DB ---
    PINECONE_API_KEY: SecretStr = Field(
        ..., description="Pinecone API Key"
    )
    PINECONE_INDEX_NAME: str = Field(
        default="mifos-knowledge-base",
        description="Name of the Pinecone index",
    )

    # Pydantic settings config
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Returns a cached instance of Settings."""
    try:
        # 1. Try loading with specific path
        return Settings()
    except ValidationError:
        # 2. Fallback: Try loading from default CWD .env if path fails
        try:
            return Settings(_env_file=".env")
        except ValidationError as e:
            logger.critical(f"❌ Configuration Error:\n{e}")
            raise RuntimeError(
                "Application failed to start. Check your .env file."
            ) from e


# --- Example usage for testing ---
if __name__ == "__main__":
    try:
        cfg = get_settings()
        print(f"✅ Configuration loaded successfully for: {cfg.APP_ENV}")
        print(f"📧 Jira Email: {cfg.JIRA_EMAIL}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")