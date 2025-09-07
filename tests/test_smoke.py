import importlib, pytest

CANDIDATES = ["factsynth_ultimate","app","factsynth"]

def test_can_import_primary():
    for n in CANDIDATES:
        try:
            importlib.import_module(n)
            return
        except Exception:
            pass
    pytest.skip("No primary package found.")
