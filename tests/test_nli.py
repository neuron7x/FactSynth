import asyncio

from app.services.nli import NLI


def test_nli_uses_async_classifier():
    async def classifier(p: str, h: str) -> float:
        return 0.42

    nli = NLI(classifier)
    score = asyncio.run(nli.classify("a", "b"))
    assert score == 0.42


def test_nli_fallback_on_error():
    async def failing_classifier(p: str, h: str) -> float:
        raise RuntimeError("boom")

    nli = NLI(failing_classifier)
    score = asyncio.run(nli.classify("Cats are animals", "Cats are animals"))
    assert score > 0.9
