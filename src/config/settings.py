from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SERVE_FRONTEND: bool = True

    # Gemini
    GEMINI_API_KEY: str = Field(
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0

    # ChromaDB
    CHROMA_DB_PATH: str = "./.chroma_db"
    CHROMA_COLLECTION_NAME: str = "mtg_rules"

    # LangSmith observability
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "prueba-turing"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
