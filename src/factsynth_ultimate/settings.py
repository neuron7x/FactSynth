from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    API_KEY: str = "change-me"
    MAX_BODY_BYTES: int = 256_000
    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    RATE_WINDOW_SEC: int = 10
    RATE_MAX_REQ: int = 60
    JWT_PUBLIC_KEY: str | None = None
    JWT_ALG: str = "RS256"
    JWT_REQUIRED_AUD: str | None = None
    model_config = {"env_file": ".env", "extra": "ignore"}
