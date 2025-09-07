from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass
class Settings:
    env: str = os.getenv("ENV", "dev")
    https_redirect: bool = os.getenv("HTTPS_REDIRECT", "false").lower() == "true"
    cors_allow_origins: str = os.getenv("CORS_ALLOW_ORIGINS", "*")
    auth_header_name: str = os.getenv("AUTH_HEADER_NAME", "x-api-key")
    skip_auth_paths: str = os.getenv("SKIP_AUTH_PATHS", "/v1/healthz,/metrics")
    ratelimit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    health_tcp_checks: str = os.getenv("HEALTH_TCP_CHECKS", "")

def load_settings() -> Settings:
    return Settings()
