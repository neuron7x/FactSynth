import logging

import pytest

from factsynth_ultimate.services.nli import NLI

EXPECTED_SCORE = 0.42
THRESHOLD = 0.9


@pytest.mark.anyio
async def test_nli_uses_async_classifier(httpx_mock):
    httpx_mock.reset()
    httpx_mock._options.assert_all_responses_were_requested = False

    async def classifier(_p: str, _h: str) -> float:
        return EXPECTED_SCORE

    nli = NLI(classifier)
    score = await nli.classify("a", "b")
    assert score == EXPECTED_SCORE


@pytest.mark.anyio
async def test_nli_fallback_on_error(httpx_mock, caplog):
    httpx_mock.reset()
    httpx_mock._options.assert_all_responses_were_requested = False

    async def failing_classifier(_p: str, _h: str) -> float:
        raise RuntimeError("boom")

    nli = NLI(failing_classifier)
    with caplog.at_level(logging.ERROR):
        score = await nli.classify(
            "Cats are animals", "Cats are animals", request_id="RID-123"
        )
    assert score > THRESHOLD
    record = next(r for r in caplog.records if r.message == "classifier_error")
    assert record.request_id == "RID-123"


@pytest.mark.anyio
async def test_nli_fallback_on_custom_classifier_error(httpx_mock):
    httpx_mock.reset()
    httpx_mock._options.assert_all_responses_were_requested = False

    class CustomError(Exception):
        pass

    class CustomClassifier:
        async def __call__(self, _p: str, _h: str) -> float:
            raise CustomError("boom")

    nli = NLI(CustomClassifier())
    score = await nli.classify("Cats are animals", "Cats are animals")
    assert score > THRESHOLD
