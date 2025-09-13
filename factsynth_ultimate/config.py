from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FactSynth"
    app_version: str = "0.1.0"
    env: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./data.db"
    redis_url: str | None = "redis://localhost:6379/0"
    rate_limit: str = "60/minute"
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FACTSYNTH_")


settings = Settings()
