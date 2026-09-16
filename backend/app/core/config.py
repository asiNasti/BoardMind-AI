from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    http_timeout: float = 10.0
    database_url: str = "postgresql+asyncpg://boardmind:boardmind@localhost:5432/boardmind"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()