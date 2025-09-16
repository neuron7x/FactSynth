"""Command-line interface for managing FactSynth configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from factsynth_ultimate.config import (
    ConfigError,
    add_callback_host,
    clear_retriever,
    configure_retriever,
    load_config,
    remove_callback_host,
)
from factsynth_ultimate.services.retrievers.registry import available_retriever_names


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

    retriever_parser = subparsers.add_parser(
        "retriever", help="Manage document retriever configuration"
    )
    retriever_sub = retriever_parser.add_subparsers(dest="retriever_command")

    retriever_set = retriever_sub.add_parser(
        "set", help="Activate a retriever discovered via entry points"
    )
    retriever_set.add_argument("name", help="Entry point name of the retriever to activate")
    retriever_set.add_argument(
        "-o",
        "--option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Pass configuration option to the retriever (can be repeated)",
    )
    retriever_set.add_argument(
        "--merge",
        action="store_true",
        help="Merge options with existing configuration instead of replacing",
    )
    retriever_set.set_defaults(func=_retriever_set)

    retriever_clear = retriever_sub.add_parser(
        "clear", help="Remove the configured retriever"
    )
    retriever_clear.set_defaults(func=_retriever_clear)

    retriever_show = retriever_sub.add_parser(
        "show", help="Display the current retriever configuration"
    )
    retriever_show.set_defaults(func=_retriever_show)

    retriever_list = retriever_sub.add_parser(
        "list", help="List retrievers discovered via entry points"
    )
    retriever_list.set_defaults(func=_retriever_list)

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


def _retriever_set(args: argparse.Namespace) -> int:
    name_raw: str = args.name.strip()
    if not name_raw:
        print("error: retriever name must not be empty", file=sys.stderr)
        return 2

    try:
        options = _parse_option_assignments(args.option or [])
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cfg_path: Path | None = args.config
    try:
        config = configure_retriever(
            name_raw,
            options=options if options or not args.merge else None,
            path=cfg_path,
            merge=bool(args.merge),
        )
    except (ConfigError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:  # pragma: no cover - filesystem failures
        print(f"error: failed to update configuration: {exc}", file=sys.stderr)
        return 2

    print(f"Retriever '{config.RETRIEVER_NAME}' configured.")
    if config.RETRIEVER_OPTIONS:
        options_json = json.dumps(config.RETRIEVER_OPTIONS, indent=2, sort_keys=True)
        print("Options:")
        print(options_json)
    else:
        print("Options: <none>")
    return 0


def _retriever_clear(args: argparse.Namespace) -> int:
    cfg_path: Path | None = args.config
    try:
        clear_retriever(cfg_path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:  # pragma: no cover - filesystem failures
        print(f"error: failed to update configuration: {exc}", file=sys.stderr)
        return 2

    print("Retriever configuration cleared.")
    return 0


def _retriever_show(args: argparse.Namespace) -> int:
    cfg_path: Path | None = args.config
    try:
        config = load_config(cfg_path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:  # pragma: no cover - filesystem failures
        print(f"error: failed to read configuration: {exc}", file=sys.stderr)
        return 2

    name = config.RETRIEVER_NAME or "<none>"
    print(f"Active retriever: {name}")
    if config.RETRIEVER_OPTIONS:
        options_json = json.dumps(config.RETRIEVER_OPTIONS, indent=2, sort_keys=True)
        print("Options:")
        print(options_json)
    else:
        print("Options: <none>")
    return 0


def _retriever_list(args: argparse.Namespace) -> int:
    try:
        names = available_retriever_names()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"error: failed to list retrievers: {exc}", file=sys.stderr)
        return 2

    if not names:
        print("No retrievers discovered.")
        return 0

    print("Discovered retrievers:")
    for name in names:
        print(f" - {name}")
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


def _parse_option_assignments(values: Sequence[str]) -> dict[str, Any]:
    """Parse ``KEY=VALUE`` assignments passed on the command line."""

    options: dict[str, Any] = {}
    for item in values:
        text = item.strip()
        if not text:
            continue
        if "=" not in text:
            raise ValueError(f"Invalid option '{item}'; expected KEY=VALUE")
        key, value = text.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("Option key must not be empty")
        options[key] = _parse_option_value(value)
    return options


def _parse_option_value(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


if __name__ == "__main__":  # pragma: no cover - manual execution
    sys.exit(main())
