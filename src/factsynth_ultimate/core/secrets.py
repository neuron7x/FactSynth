from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

def read_api_key(env: str, env_file: str, default: Optional[str], env_name: str) -> str:
    """
    Порядок: файл секрету -> VAULT -> env -> default (допускається лише у dev).
    """
    # 1) файл
    p = os.getenv(env_file)
    if p and Path(p).exists():
        return Path(p).read_text(encoding="utf-8").strip()
    # 2) VAULT (опційно)
    if os.getenv("VAULT_ADDR") and os.getenv("VAULT_TOKEN") and os.getenv("VAULT_PATH"):
        try:
            import hvac  # optional
            client = hvac.Client(url=os.getenv("VAULT_ADDR"), token=os.getenv("VAULT_TOKEN"))
            secret = client.secrets.kv.v2.read_secret_version(path=os.getenv("VAULT_PATH"))
            val = secret["data"]["data"].get(env_name)
            if val: return str(val)
        except Exception:
            pass
    # 3) env
    val = os.getenv(env)
    if val: return val
    # 4) default (тільки не-prod)
    return default or ""
