"""WebSocket authentication utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping

from ..core.settings import load_settings


@dataclass(frozen=True, slots=True)
class WebSocketUser:
    """Immutable user record returned after successful authentication."""

    api_key: str
    user: Mapping[str, Any]
    organization: Mapping[str, Any]
    status: str = "active"

    @property
    def user_id(self) -> str:
        """Best-effort identifier for the authenticated user."""

        for key in ("id", "user_id", "email", "name"):
            value = self.user.get(key)
            if value:
                return str(value)
        return ""

    @property
    def organization_slug(self) -> str:
        """Return the slug-like identifier for the organization."""

        for key in ("slug", "key", "id", "name"):
            value = self.organization.get(key)
            if value:
                return str(value)
        return ""

    @property
    def organization_name(self) -> str:
        """Return the human friendly organization name if available."""

        value = self.organization.get("name")
        if value:
            return str(value)
        return self.organization_slug


class WebSocketAuthError(Exception):
    """Exception raised when websocket authentication fails."""

    def __init__(self, code: int, reason: str) -> None:
        super().__init__(reason)
        self.code = int(code)
        self.reason = reason


_REGISTRY: MutableMapping[str, WebSocketUser] | None = None


def _default_registry() -> MutableMapping[str, WebSocketUser]:
    settings = load_settings()
    key = settings.api_key
    user = WebSocketUser(
        api_key=key,
        user={"id": "default", "name": "Default User"},
        organization={"slug": "default", "name": "Default Org"},
        status="active",
    )
    return {key.casefold(): user}


def set_ws_registry(registry: Mapping[str, WebSocketUser]) -> None:
    """Override the authentication registry (used by tests)."""

    global _REGISTRY
    _REGISTRY = {key.casefold(): value for key, value in registry.items()}


def reset_ws_registry() -> None:
    """Reset the registry to its default lazy-loaded state."""

    global _REGISTRY
    _REGISTRY = None


def _registry() -> MutableMapping[str, WebSocketUser]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _default_registry()
    return _REGISTRY


def authenticate_ws(api_key: str | None) -> WebSocketUser:
    """Validate ``api_key`` and return the associated :class:`WebSocketUser`."""

    key = (api_key or "").strip()
    if not key:
        raise WebSocketAuthError(4401, "Missing API key")

    entry = _registry().get(key.casefold())
    if entry is None:
        raise WebSocketAuthError(4401, "Invalid API key")

    if not entry.user:
        raise WebSocketAuthError(4401, "User data required")

    if not entry.organization or not entry.organization_slug:
        raise WebSocketAuthError(4403, "Organization required")

    if entry.status.casefold() not in {"active", "enabled"}:
        raise WebSocketAuthError(4429, "API key disabled")

    return entry


__all__ = [
    "WebSocketAuthError",
    "WebSocketUser",
    "authenticate_ws",
    "reset_ws_registry",
    "set_ws_registry",
]
