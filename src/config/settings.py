from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    api_url: str = "http://localhost:8000"
    chroma_db_path: str = "./.chroma_db"
    chroma_collection_name: str = "mtg_rules"


@lru_cache
def get_settings() -> Settings:
    return Settings()
