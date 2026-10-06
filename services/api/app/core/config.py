"""Application configuration loaded from environment variables."""

import secrets
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ResQGrid AI application settings."""

    # ---- Application ----
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_SECRET_KEY: str = "change-me-to-a-random-string"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ---- Database ----
    DATABASE_URL: str = "postgresql+asyncpg://resqgrid:resqgrid_dev_password@localhost:5432/resqgrid_ai"

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def _ensure_asyncpg(cls, v: str) -> str:
        """Supabase/Railway/Render often provide postgresql:// URLs.

        SQLAlchemy async requires postgresql+asyncpg://, so convert automatically.
        """
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ---- JWT ----
    JWT_SECRET: str = Field(default="", repr=False)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- AI / Model Studio ----
    DASHSCOPE_API_KEY: str = ""
    MODEL_STUDIO_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_STUDIO_MODEL: str = "qwen-plus"

    # ---- Google Gemini ----
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # ---- Object Storage ----
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET: str = "resqgrid-evidence"
    OSS_REGION: str = "ap-southeast-1"
    OSS_ENDPOINT: str = "https://oss-ap-southeast-1.aliyuncs.com"

    UPLOAD_DIR: Path = Path(__file__).resolve().parents[2] / "uploads"
    MAX_UPLOAD_BYTES: int = Field(10 * 1024 * 1024, ge=1024, le=25 * 1024 * 1024)
    MAX_IMAGE_PIXELS: int = Field(20_000_000, ge=1, le=40_000_000)
    EVIDENCE_USER_QUOTA_BYTES: int = Field(100 * 1024 * 1024, ge=1024)
    EVIDENCE_INCIDENT_LIMIT: int = Field(50, ge=1, le=500)

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:3000"

    # ---- Logging ----
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ---- Priority Engine Weights (configurable) ----
    WEIGHT_LIFE_RISK: float = 0.30
    WEIGHT_MEDICAL_URGENCY: float = 0.20
    WEIGHT_PEOPLE_AT_RISK: float = 0.15
    WEIGHT_ENVIRONMENTAL_RISK: float = 0.15
    WEIGHT_TIME_SENSITIVITY: float = 0.10
    WEIGHT_EVIDENCE_CONFIDENCE: float = 0.10

    @model_validator(mode="after")
    def validate_security_settings(self):
        weak_secret = (
            len(self.JWT_SECRET.encode("utf-8")) < 32
            or any(marker in self.JWT_SECRET.lower() for marker in ("change-me", "changeme", "your-secret"))
        )
        if weak_secret:
            if self.APP_ENV.lower() not in {"development", "test"}:
                raise ValueError("Set JWT_SECRET to a random secret of at least 32 bytes before starting the API")
            # Local demos remain usable without a shared, publicly known signing key.
            self.JWT_SECRET = secrets.token_urlsafe(48)
        if self.JWT_ALGORITHM != "HS256":
            raise ValueError("JWT_ALGORITHM must be HS256")
        if any(origin.strip() == "*" for origin in self.CORS_ORIGINS.split(",")):
            raise ValueError("CORS_ORIGINS must list explicit origins")
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "hide_input_in_errors": True}


settings = Settings()
