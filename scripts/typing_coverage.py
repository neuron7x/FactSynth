"""Compute the percentage of functions with complete type annotations."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class FunctionStats:
    """Aggregate counters for typed versus total functions."""

    typed: int = 0
    total: int = 0

    def update(self, is_typed: bool) -> None:
        self.total += 1
        if is_typed:
            self.typed += 1

    def merge(self, other: FunctionStats) -> None:
        self.typed += other.typed
        self.total += other.total

    @property
    def percentage(self) -> float:
        return 0.0 if self.total == 0 else (self.typed / self.total) * 100.0


def _annotate_parents(node: ast.AST) -> None:
    for child in ast.iter_child_nodes(node):
        child.parent = node  # type: ignore[attr-defined]
        _annotate_parents(child)


def _iter_functions(tree: ast.AST) -> Iterable[ast.FunctionDef | ast.AsyncFunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _is_method(node: ast.AST) -> bool:
    return isinstance(getattr(node, "parent", None), ast.ClassDef)


def _parameter_is_typed(arg: ast.arg, ignore_untyped_self: bool) -> bool:
    if arg.annotation is not None:
        return True
    if ignore_untyped_self and arg.arg in {"self", "cls"}:
        return True
    return False


def _function_is_typed(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    is_method = _is_method(node)
    positional = list(node.args.posonlyargs) + list(node.args.args)
    ignore_first = is_method and bool(positional)

    for index, arg in enumerate(positional):
        if not _parameter_is_typed(arg, ignore_untyped_self=ignore_first and index == 0):
            return False

    for arg in node.args.kwonlyargs:
        if not _parameter_is_typed(arg, ignore_untyped_self=False):
            return False

    if node.args.vararg and node.args.vararg.annotation is None:
        return False

    if node.args.kwarg and node.args.kwarg.annotation is None:
        return False

    if node.returns is None and node.name != "__init__":
        return False

    return True


def analyse_file(path: Path) -> FunctionStats:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    _annotate_parents(tree)
    stats = FunctionStats()
    for fn in _iter_functions(tree):
        stats.update(_function_is_typed(fn))
    return stats


def iter_python_files(path: Path) -> Iterable[Path]:
    if path.is_dir():
        yield from path.rglob("*.py")
    elif path.suffix == ".py":
        yield path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("src/factsynth_ultimate")],
        help="Directories or files to inspect",
    )
    args = parser.parse_args()

    stats = FunctionStats()
    for path in args.paths:
        for file_path in iter_python_files(path):
            stats.merge(analyse_file(file_path))

    print(f"Typed functions: {stats.typed}/{stats.total} ({stats.percentage:.2f}%)")


if __name__ == "__main__":
    main()
