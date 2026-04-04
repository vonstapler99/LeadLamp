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

    # Twilio (SMS). Same pattern as DATABASE_URL: names in code are readable;
    # .env uses the UPPER_SNAKE names your hosting provider expects.
    #
    # WHY load secrets here (not scattered os.getenv calls):
    # - One place to validate: app fails fast at startup if Twilio vars are missing.
    # - Services import `settings` only — easier to test (swap settings in tests).
    twilio_account_sid: str = Field(alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(alias="TWILIO_AUTH_TOKEN")
    # Your Twilio phone number that sends SMS (E.164, e.g. +15551234567).
    twilio_from_number: str = Field(alias="TWILIO_FROM_NUMBER")

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
