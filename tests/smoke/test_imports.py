import importlib

CANDIDATES = ("factsynth_ultimate", "factsynth")


def test_import_core():
    for name in CANDIDATES:
        try:
            importlib.import_module(name)
            break
        except ImportError:
            pass
    else:
        raise AssertionError(f"Cannot import any of {CANDIDATES}")
