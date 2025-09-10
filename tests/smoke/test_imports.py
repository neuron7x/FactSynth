import pytest

@pytest.mark.parametrize("name", ["factsynth_ultimate", "factsynth"])
def test_import_core(name):
    pytest.importorskip(name)

