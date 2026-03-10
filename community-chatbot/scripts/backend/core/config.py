from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Community AI Backend"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # GitHub App Settings
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_REPOSITORY: Optional[str] = None
    GITHUB_BRANCH: Optional[str] = None
    GITHUB_BASE_BRANCH: Optional[str] = None
    GITHUB_APP_PRIVATE_KEY: Optional[str] = None

    # Jira Settings
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_USERNAME: Optional[str] = None
    JIRA_INSTANCE_URL: Optional[str] = None
    JIRA_CLOUD: Optional[bool] = None
    
    # Slack Settings
    SLACK_BOT_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
