import importlib

CANDIDATES = ("factsynth_ultimate", "factsynth")
def test_import_core():
    ok = False
    for name in CANDIDATES:
        try:
            importlib.import_module(name)
            ok = True
            break
        except Exception:
            continue
    assert ok, f"Cannot import any of {CANDIDATES}"
