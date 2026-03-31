from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings.

    BaseSettings behavior:
    - Reads from environment variables first.
    - Reads from .env as a fallback (configured below).
    - Performs parsing and validation, so bad/missing values fail fast.
    """

    # DATABASE_URL from environment/.env maps to this field because
    # case_sensitive=False and pydantic converts naming styles.
    database_url: str

    # model_config controls how BaseSettings loads values.
    model_config = SettingsConfigDict(
        # Load a local .env file in development.
        env_file=".env",
        # Standard text encoding for the .env file.
        env_file_encoding="utf-8",
        # Accept DATABASE_URL for database_url.
        case_sensitive=False,
        # Ignore any extra keys we are not explicitly modeling yet.
        extra="ignore",
    )


# Single shared settings instance imported by the rest of the app.
settings = Settings()
