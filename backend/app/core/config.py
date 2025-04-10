"""
Configuration module for the application.

This module handles loading environment variables and providing configuration settings
for the application.
"""
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path # Import Path

from pydantic import AnyHttpUrl, PostgresDsn, validator, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict # Import SettingsConfigDict

# Define the path to the .env file in the project root
# Assumes config.py is in backend/app/core/
# Go up three levels to reach the project root where .env should be
env_path = Path(__file__).parent.parent.parent.parent / '.env'

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        PROJECT_NAME: Name of the project
        API_V1_STR: API version prefix
        SECRET_KEY: Secret key for JWT token generation
        ACCESS_TOKEN_EXPIRE_MINUTES: Expiration time for access tokens in minutes
        BACKEND_CORS_ORIGINS: Comma-separated string of origins allowed for CORS
        DATABASE_URL: PostgreSQL database connection string
        FIRST_SUPERUSER_EMAIL: Email for the first admin user created on startup
        FIRST_SUPERUSER_PASSWORD: Password for the first admin user created on startup
        LINKEDIN_CLIENT_ID: Client ID for LinkedIn OAuth
        LINKEDIN_CLIENT_SECRET: Client Secret for LinkedIn OAuth
        LINKEDIN_REDIRECT_URI: Redirect URI configured in LinkedIn App
        FRONTEND_URL_BASE: Base URL of the frontend application (for redirects)
    """
    PROJECT_NAME: str = "Winning Sales Content Hub"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS
    # Read as a string, split later in main.py
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database
    DATABASE_URL: str

    # First Superuser (Admin) - Added for automatic creation on startup
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"

    # LinkedIn Integration (Required)
    LINKEDIN_CLIENT_ID: str
    LINKEDIN_CLIENT_SECRET: str
    LINKEDIN_REDIRECT_URI: str # e.g., http://localhost:8000/api/v1/linkedin/connect/callback

    # Frontend URL (for redirects etc.)
    FRONTEND_URL_BASE: str = "http://localhost:3000" # Default for local dev

    # Use model_config instead of Config class for Pydantic v2+
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=env_path, # Explicitly set the path
        env_file_encoding='utf-8',
        extra='ignore' # Ignore extra variables found in .env file
    )

# Create settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"DEBUG: Error loading Settings: {e}")
    # Attempt to find the .env path manually for debugging
    try:
        from pathlib import Path
        potential_path = Path('.env').resolve()
        print(f"DEBUG: Potential .env path based on CWD: {potential_path}")
        if not potential_path.exists():
             # Check parent directories if needed
             pass
    except Exception:
        pass # Ignore errors during debug printing
    raise e # Re-raise the original error
