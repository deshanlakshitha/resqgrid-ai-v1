"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ResQGrid AI application settings."""

    # ---- Application ----
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change-me-to-a-random-string"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ---- Database ----
    DATABASE_URL: str = "postgresql+asyncpg://resqgrid:resqgrid_dev_password@localhost:5432/resqgrid_ai"

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- JWT ----
    JWT_SECRET: str = "change-me-to-a-secure-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- AI / Model Studio ----
    DASHSCOPE_API_KEY: str = ""
    MODEL_STUDIO_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_STUDIO_MODEL: str = "qwen-plus"

    # ---- Object Storage ----
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET: str = "resqgrid-evidence"
    OSS_REGION: str = "ap-southeast-1"
    OSS_ENDPOINT: str = "https://oss-ap-southeast-1.aliyuncs.com"

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
