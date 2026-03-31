from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Explicitly load the project's .env file into process environment variables.
# This makes behavior consistent for app runtime, scripts, and Alembic CLI.
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """
    Central application settings.

    BaseSettings behavior:
    - Reads from environment variables first.
    - Reads from .env as a fallback (configured below).
    - Performs parsing and validation, so bad/missing values fail fast.
    """

    # Explicitly bind the expected env var name used in .env.
    database_url: str = Field(alias="DATABASE_URL")

    # model_config controls how BaseSettings loads values.
    model_config = SettingsConfigDict(
        # Keep the env file path explicit and absolute for reliability.
        env_file=PROJECT_ROOT / ".env",
        # Standard text encoding for the .env file.
        env_file_encoding="utf-8",
        # Accept DATABASE_URL for database_url.
        case_sensitive=False,
        # Ignore any extra keys we are not explicitly modeling yet.
        extra="ignore",
    )


# Single shared settings instance imported by the rest of the app.
settings = Settings()
