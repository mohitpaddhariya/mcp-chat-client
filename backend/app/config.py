"""Configuration for the backend application."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    
    # Model Configuration
    model_name: str = Field(default="gemini-2.0-flash", alias="MODEL_NAME")
    
    # Filesystem MCP - allowed directory path
    filesystem_allowed_path: str = Field(
        default="/Users/mohitpaddhariya",
        alias="FILESYSTEM_ALLOWED_PATH"
    )
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
