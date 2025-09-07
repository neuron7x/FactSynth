from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass
class Settings:
    api_key: str = "change-me"


def load_settings() -> Settings:
    return Settings(api_key=os.getenv("API_KEY", "change-me"))
