"""Authentication helpers for websocket connections."""

from .ws import (
    WebSocketAuthError,
    WebSocketUser,
    authenticate_ws,
    reset_ws_registry,
    set_ws_registry,
)

__all__ = [
    "WebSocketAuthError",
    "WebSocketUser",
    "authenticate_ws",
    "reset_ws_registry",
    "set_ws_registry",
]
