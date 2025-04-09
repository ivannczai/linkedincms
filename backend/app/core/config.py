"""
Configuration module for the application.

This module handles loading environment variables and providing configuration settings
for the application.
"""
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path # Import Path
from dotenv import load_dotenv # Import load_dotenv

from pydantic import AnyHttpUrl, PostgresDsn, validator, EmailStr
from pydantic_settings import BaseSettings

# Explicitly load .env file from project root
# Assumes config.py is in backend/app/core/, so go up 3 levels
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
# print(f"Attempting to load .env file from: {env_path}") # Debug print - Remove later
# print(f"LINKEDIN_CLIENT_ID from env: {os.getenv('LINKEDIN_CLIENT_ID')}") # Debug print - Remove later


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        PROJECT_NAME: Name of the project
        API_V1_STR: API version prefix
        SECRET_KEY: Secret key for JWT token generation
        ACCESS_TOKEN_EXPIRE_MINUTES: Expiration time for access tokens in minutes
        BACKEND_CORS_ORIGINS: List of origins that should be allowed for CORS
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
    # Type hint is List[str], pydantic-settings should handle comma-separated env var
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:5173", "http://localhost"]

    # Removed custom validator assemble_cors_origins

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

    class Config:
        """
        Pydantic configuration for Settings.
        """
        case_sensitive = True
        # env_file = ".env" # No longer needed as we load explicitly above
        env_file_encoding = 'utf-8' # Specify encoding just in case


# Create settings instance
settings = Settings()
