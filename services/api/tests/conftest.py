"""Isolated test configuration: never load developer secrets or contact services."""

import os
import secrets
from unittest.mock import patch

# Settings are imported during test collection, before fixtures can run.
with patch.dict(os.environ, {
    "APP_ENV": "test",
    "JWT_SECRET": secrets.token_urlsafe(48),
    "JWT_ALGORITHM": "HS256",
    "DATABASE_URL": "postgresql+asyncpg://test:test@127.0.0.1:1/test",
    "REDIS_URL": "redis://127.0.0.1:1/0",
    "GEMINI_API_KEY": "",
    "DASHSCOPE_API_KEY": "",
    "OSS_ACCESS_KEY_ID": "",
    "OSS_ACCESS_KEY_SECRET": "",
    "CORS_ORIGINS": "http://localhost:3000",
}), patch("pydantic_settings.sources.DotEnvSettingsSource._read_env_files", return_value={}):
    from app.core.config import settings  # noqa: F401
