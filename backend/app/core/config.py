from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application configuration.

    All configuration values are loaded from environment variables
    or the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------------------------------------------------
    # Application
    # -------------------------------------------------

    APP_NAME: str = "AGCT"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # -------------------------------------------------
    # Security
    # -------------------------------------------------

    SECRET_KEY: str = Field(...)

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -------------------------------------------------
    # PostgreSQL
    # -------------------------------------------------

    POSTGRES_HOST: str = "localhost"

    POSTGRES_PORT: int = 5432

    POSTGRES_DB: str

    POSTGRES_USER: str

    POSTGRES_PASSWORD: str

    # -------------------------------------------------
    # Redis
    # -------------------------------------------------

    REDIS_HOST: str

    REDIS_PORT: int

    # -------------------------------------------------
    # Neo4j
    # -------------------------------------------------

    NEO4J_URI: str

    NEO4J_USERNAME: str

    NEO4J_PASSWORD: str

    # -------------------------------------------------
    # Chroma
    # -------------------------------------------------

    CHROMA_HOST: str

    CHROMA_PORT: int

    # -------------------------------------------------
    # Ollama
    # -------------------------------------------------

    OLLAMA_BASE_URL: str

    DEFAULT_CHAT_MODEL: str

    DEFAULT_EMBEDDING_MODEL: str

    # -------------------------------------------------
    # Logging
    # -------------------------------------------------

    LOG_LEVEL: str = "INFO"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
    )
    @property
    def REDIS_URL(self) -> str:
        return (
            f"redis://"
            f"{self.REDIS_HOST}:"
            f"{self.REDIS_PORT}"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a singleton Settings instance.
    """
    return Settings()


settings = get_settings()