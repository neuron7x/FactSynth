from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import hvac  # type: ignore[import]
except ImportError:  # pragma: no cover - optional dependency
    hvac = None

if TYPE_CHECKING or hvac is not None:
    from hvac.exceptions import VaultError
else:

    class VaultError(Exception):
        pass


def _validate_key(key: str) -> str:
    """Ensure a real API key is set in production."""
    if os.getenv("ENV") == "prod" and key in {"", "change-me"}:
        raise RuntimeError("API key must be set in production")
    return key


def read_api_key(env: str, env_file: str, default: str | None, env_name: str) -> str:
    """Resolve API key from file, Vault, environment or default (dev only)."""
    key = ""
    # 1) file
    p = os.getenv(env_file)
    if p and Path(p).exists():
        key = Path(p).read_text(encoding="utf-8").strip()
    # 2) Vault (optional)
    elif (
        hvac is not None
        and os.getenv("VAULT_ADDR")
        and os.getenv("VAULT_TOKEN")
        and os.getenv("VAULT_PATH")
    ):
        try:
            client = hvac.Client(
                url=os.getenv("VAULT_ADDR"),
                token=os.getenv("VAULT_TOKEN"),
            )
            secret = client.secrets.kv.v2.read_secret_version(path=os.getenv("VAULT_PATH"))
            val = secret["data"]["data"].get(env_name)
            if val:
                key = str(val)
        except VaultError:
            pass
    # 3) environment
    if not key:
        val = os.getenv(env)
        if val:
            key = val
    # 4) default (non-production only)
    if not key:
        key = default or ""
    return _validate_key(key)
