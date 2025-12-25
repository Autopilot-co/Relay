"""
Relay - Application Settings
Loads configuration from environment variables
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from .env file
    
    Pydantic automatically:
    - Loads from .env file
    - Validates types
    - Provides defaults
    - Gives helpful errors if something's wrong
    """
    
    # Application
    app_name: str = "Relay"
    debug: bool = True
    port: int = 8000
    
    # Slack (Micro-Step 4 & 5)
    slack_bot_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None  # For verifying requests from Slack
    
    # n8n (will use in Step 2)
    n8n_api_url: Optional[str] = None
    n8n_api_key: Optional[str] = None
    
    # LLM APIs (will use in Step 3)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # APP_NAME or app_name both work
        extra="ignore"  # Ignore extra env vars
    )


# Create a single global settings instance
# This gets imported everywhere: from config.settings import settings
settings = Settings()

