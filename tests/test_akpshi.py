import pytest

try:
    import numpy  # noqa: F401
except ModuleNotFoundError:
    pytest.skip("numpy not installed", allow_module_level=True)

from factsynth_ultimate.akpshi.metrics import fcr, pfi, rmse

EXPECTED_FCR = 0.9
EXPECTED_PFI_CLIP = 0.5

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_metrics():
    assert round(rmse([0, 1], [0, 1]), 6) == 0.0
    assert fcr(9, 10) == EXPECTED_FCR
    assert 0 <= pfi([0.4, 0.6, 0.5]) <= 1


def test_rmse_length_mismatch():
    with pytest.raises(ValueError):
        rmse([0, 1], [0])


def test_fcr_clamps_totals():
    assert fcr(1, 0) == 1.0
    assert fcr(1, -5) == 1.0


def test_pfi_clips_scores():
    assert pfi([-0.5, 0.5, 1.5]) == EXPECTED_PFI_CLIP
