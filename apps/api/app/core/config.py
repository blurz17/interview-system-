from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "CareerPilot"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/careerpilot"
    DATABASE_TEST_URL: str = "sqlite+aiosqlite:///:memory:"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # Security
    JWT_SECRET_KEY: str = "change_this_to_a_secure_random_secret_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_DIR: str = "storage/uploads"
    STORAGE_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # Judge0 Code Execution
    JUDGE0_API_URL: str = "http://localhost:2358"
    JUDGE0_API_KEY: str = ""
    JUDGE0_TIMEOUT_SECONDS: int = 10
    JUDGE0_MEMORY_LIMIT_KB: int = 256000
    JUDGE0_CPU_TIME_LIMIT_SECONDS: int = 5
    JUDGE0_MOCK_FALLBACK: bool = True

    # AI Models & Providers
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_API_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES: int = 2
    AI_MAX_TOKENS: int = 2048
    AI_DAILY_USER_LIMIT: int = 50

    # Embeddings
    EMBEDDING_PROVIDER: str = "huggingface"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"

    # Speech
    SPEECH_PROVIDER: str = "huggingface"
    SPEECH_API_KEY: str = ""
    SPEECH_MODEL: str = "openai/whisper-large-v3-turbo"
    TTS_PROVIDER: str = "web_speech_api"
    TTS_API_KEY: str = ""
    TTS_MODEL: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
