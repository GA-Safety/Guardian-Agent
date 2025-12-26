"""
Application configuration from environment variables
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    DB_HOST: str
    DB_PORT: str = "5432"
    DB_NAME: str = "postgres"
    DB_USER: str
    DB_PASSWORD: str
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Application settings
    APP_NAME: str = "Guardian Agent API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # CORS settings (comma-separated in env, or JSON array)
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Validate required database settings
if not all([settings.DB_HOST, settings.DB_USER, settings.DB_PASSWORD]):
    raise ValueError(
        "Missing required database environment variables. "
        "Set DB_HOST, DB_USER, and DB_PASSWORD in .env file"
    )

