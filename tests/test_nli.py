import asyncio

from factsynth_ultimate.services.nli import NLI


def test_nli_uses_async_classifier():
    async def classifier(_p: str, _h: str) -> float:
        return 0.42

    nli = NLI(classifier)
    score = asyncio.run(nli.classify("a", "b"))
    assert score == 0.42  # noqa: PLR2004


def test_nli_fallback_on_error():
    async def failing_classifier(_p: str, _h: str) -> float:
        raise RuntimeError("boom")

    nli = NLI(failing_classifier)
    score = asyncio.run(nli.classify("Cats are animals", "Cats are animals"))
    assert score > 0.9  # noqa: PLR2004
