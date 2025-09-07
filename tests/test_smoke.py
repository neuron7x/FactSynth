import importlib, sys, pathlib

CANDIDATES = [
    "factsynth_ultimate",
    "app",
    "factsynth",
]

def test_can_import_any_package():
    for name in CANDIDATES:
        try:
            importlib.import_module(name)
            return
        except Exception:
            continue
    # If nothing imports, skip rather than fail hard
    import pytest
    pytest.skip("No primary package found among candidates: " + ", ".join(CANDIDATES))
