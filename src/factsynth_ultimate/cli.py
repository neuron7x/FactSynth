import argparse
import json
import sys

from . import __version__
from .service import synthesize


def main(argv=None):
    argv = argv or sys.argv[1:]
    p = argparse.ArgumentParser(prog="factsynth", description="FactSynth CLI")
    sub = p.add_subparsers(dest="cmd")
    g = sub.add_parser("gen", help="Generate output")
    g.add_argument("--prompt", required=True)
    g.add_argument("--max-tokens", type=int, default=128)
    sub.add_parser("version", help="Show version")
    a = p.parse_args(argv)
    if a.cmd == "gen":
        print(json.dumps({"output": synthesize(a.prompt, a.max_tokens)}, ensure_ascii=False))
        return 0
    if a.cmd == "version":
        print(__version__)
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
