import os
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service & Network
    APP_NAME: str = "IncuBrix Prompt-Based Video Editing Engine"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Directory Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    TEMP_DIR: Path = Field(default_factory=lambda: Path(os.getenv("TEMP_DIR", "temp_data")))
    STORAGE_DIR: Path = Field(default_factory=lambda: Path(os.getenv("STORAGE_DIR", "storage_data")))
    OUTPUT_DIR: Path = Field(default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "outputs")))

    # Security & Idempotency
    WEBHOOK_HMAC_SECRET: str = "incubrix-super-secret-hmac-key"
    IDEMPOTENCY_TTL_SECONDS: int = 86400  # 24 hours
    MAX_UPLOAD_SIZE_BYTES: int = 1024 * 1024 * 500  # 500 MB
    DOWNLOAD_TIMEOUT_SECONDS: int = 60

    # Job & Async Worker Configuration
    ASYNC_THRESHOLD_SECONDS: float = 2.0
    JOB_POLL_INTERVAL_SECONDS: float = 0.5
    MAX_CONCURRENT_JOBS: int = 4

    # Editing & Timeline Policy
    # When user says "at 1:20" after cuts, stated policy: "current" (default preview timeline time) or "source"
    DEFAULT_TIME_POLICY: Literal["current", "source"] = "current"
    MIN_CAPTION_DURATION_MS: int = 700  # Advanced feature A1: readable minimum ~0.7s
    DEFAULT_SILENCE_THRESHOLD_DB: float = -35.0
    DEFAULT_MIN_SILENCE_DURATION_MS: int = 500  # 0.5s

    # Providers
    STT_PROVIDER: Literal["mock", "whisper"] = "mock"
    STT_MODEL_SIZE: str = "base"
    USE_GPU: bool = False

    # S3 / MinIO Configuration
    S3_ENABLED: bool = False
    S3_ENDPOINT: str = "localhost:9000"
    S3_BUCKET: str = "incubrix-videos"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_USE_SSL: bool = False


settings = Settings()

# Ensure directories exist
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
