import os
import logging
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, ValidationError

# Setup basic logging for config errors
logger = logging.getLogger("mifos-config")

# --- PATH CORRECTION LOGIC ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
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
        ...,
        description="Channel ID where the Watchdog posts intelligence reports",
    )
    SLACK_ALERT_CHANNEL_ID: str = Field(
        ...,
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

    # [FIX] Map 'JIRA_EMAIL' from .env to 'JIRA_USERNAME' for the Python code
    JIRA_USERNAME: str = Field(
        ...,
        alias="JIRA_EMAIL",
        description="Jira username/email (Mapped from JIRA_EMAIL in .env)"
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
        extra="ignore",
        populate_by_name=True  # Allows using either JIRA_USERNAME or JIRA_EMAIL
    )


@lru_cache
def get_settings() -> Settings:
    """Returns a cached instance of Settings."""
    try:
        return Settings()
    except ValidationError as e:
        logger.critical(f"❌ Configuration Error:\n{e}")
        logger.critical(f"🔍 Looked for .env at: {DOTENV_PATH}")
        raise RuntimeError(
            "Application failed to start due to missing or invalid environment variables."
        ) from e


# --- Example usage for testing ---
if __name__ == "__main__":
    try:
        cfg = get_settings()
        print(f"✅ Configuration loaded successfully for: {cfg.APP_ENV}")
        # Verify the mapping worked
        print(f"📧 Jira User: {cfg.JIRA_USERNAME}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
