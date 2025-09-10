import importlib
import pytest

CANDIDATES = ("factsynth_ultimate", "factsynth")


def test_import_core():
    for name in CANDIDATES:
        try:
            importlib.import_module(name)
            break
        except ImportError:
            pass
    else:
        pytest.fail(f"Cannot import any of {CANDIDATES}")
