"""Command-line interface for managing FactSynth configuration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from factsynth_ultimate.config import (
    ConfigError,
    add_callback_host,
    load_config,
    remove_callback_host,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fsctl", description="FactSynth control utility")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to the configuration file (defaults to FACTSYNTH_CONFIG_PATH or ~/.factsynth/config.json)",
    )

    subparsers = parser.add_subparsers(dest="command")

    callbacks_parser = subparsers.add_parser(
        "callbacks", help="Manage callback URL allowlists"
    )
    callbacks_sub = callbacks_parser.add_subparsers(dest="callbacks_command")

    allow_parser = callbacks_sub.add_parser("allow", help="Allow callbacks to the specified host")
    allow_parser.add_argument("host", help="Hostname to add to the callback allowlist")
    allow_parser.set_defaults(func=_callbacks_allow)

    remove_parser = callbacks_sub.add_parser(
        "remove", help="Remove callbacks to the specified host"
    )
    remove_parser.add_argument("host", help="Hostname to remove from the callback allowlist")
    remove_parser.set_defaults(func=_callbacks_remove)

    list_parser = callbacks_sub.add_parser(
        "list", help="Show the configured callback allowlist"
    )
    list_parser.set_defaults(func=_callbacks_list)

    return parser


def _callbacks_allow(args: argparse.Namespace) -> int:
    host_raw: str = args.host.strip()
    if not host_raw:
        print("error: host must not be empty", file=sys.stderr)
        return 2

    normalized = host_raw.lower()
    cfg_path: Path | None = args.config
    try:
        config = add_callback_host(normalized, path=cfg_path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:  # pragma: no cover - filesystem failures
        print(f"error: failed to update configuration: {exc}", file=sys.stderr)
        return 2

    allowlist = ", ".join(config.CALLBACK_URL_ALLOWED_HOSTS) or "<empty>"
    print(f"Callback host '{normalized}' allowed.")
    print(f"Current callback allowlist: {allowlist}")
    return 0


def _callbacks_remove(args: argparse.Namespace) -> int:
    host_raw: str = args.host.strip()
    if not host_raw:
        print("error: host must not be empty", file=sys.stderr)
        return 2

    normalized = host_raw.lower()
    cfg_path: Path | None = args.config
    try:
        config = remove_callback_host(normalized, path=cfg_path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:  # pragma: no cover - filesystem failures
        print(f"error: failed to update configuration: {exc}", file=sys.stderr)
        return 2

    allowlist = ", ".join(config.CALLBACK_URL_ALLOWED_HOSTS) or "<empty>"
    print(f"Callback host '{normalized}' removed.")
    print(f"Current callback allowlist: {allowlist}")
    return 0


def _callbacks_list(args: argparse.Namespace) -> int:
    cfg_path: Path | None = args.config
    try:
        config = load_config(cfg_path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:  # pragma: no cover - filesystem failures
        print(f"error: failed to read configuration: {exc}", file=sys.stderr)
        return 2

    allowlist = ", ".join(config.CALLBACK_URL_ALLOWED_HOSTS) or "<empty>"
    print(f"Current callback allowlist: {allowlist}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point for the ``fsctl`` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "func", None)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":  # pragma: no cover - manual execution
    sys.exit(main())
