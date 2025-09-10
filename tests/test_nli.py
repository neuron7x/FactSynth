import asyncio

from app.services.nli import NLI

EXPECTED_SCORE = 0.42
HIGH_THRESHOLD = 0.9

def test_nli_uses_async_classifier():
    async def classifier(_p: str, _h: str) -> float:
        return EXPECTED_SCORE

    nli = NLI(classifier)
    score = asyncio.run(nli.classify("a", "b"))
    assert score == EXPECTED_SCORE


def test_nli_fallback_on_error():
    async def failing_classifier(_p: str, _h: str) -> float:
        raise RuntimeError("boom")

    nli = NLI(failing_classifier)
    score = asyncio.run(nli.classify("Cats are animals", "Cats are animals"))
    assert score > HIGH_THRESHOLD
