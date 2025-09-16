from __future__ import annotations

import asyncio

import pytest

from factsynth_ultimate.stream import FactStreamChunk, _chunk_text, stream_facts


pytestmark = [
    pytest.mark.usefixtures("assert_all_responses_were_requested"),
    pytest.mark.httpx_mock(assert_all_responses_were_requested=False),
]


class StubPipeline:
    def __init__(self, fragments: list[str]) -> None:
        self.fragments = fragments

    def run(self, query: str) -> str:
        return "".join(self.fragments)

    async def arun(self, query: str):
        for fragment in self.fragments:
            await asyncio.sleep(0)
            yield fragment


@pytest.mark.asyncio
async def test_stream_facts_incremental_chunks() -> None:
    fragments = ["alpha beta ", "gamma delta", " epsilon zeta"]
    pipeline = StubPipeline(fragments)
    chunk_size = 6
    expected = _chunk_text(pipeline.run("ignored"), limit=chunk_size)

    chunks: list[FactStreamChunk] = []
    async for chunk in stream_facts(pipeline, "ignored", chunk_size=chunk_size):
        chunks.append(chunk)

    assert [chunk.index for chunk in chunks] == list(range(len(expected)))
    assert [chunk.text for chunk in chunks] == expected


@pytest.mark.asyncio
async def test_stream_facts_resumes_from_start_at() -> None:
    fragments = ["alpha beta ", "gamma delta", " epsilon zeta"]
    pipeline = StubPipeline(fragments)
    chunk_size = 6
    expected = _chunk_text(pipeline.run("ignored"), limit=chunk_size)

    collected: list[FactStreamChunk] = []
    async for chunk in stream_facts(pipeline, "ignored", chunk_size=chunk_size):
        collected.append(chunk)
        if len(collected) == 2:
            break

    assert [chunk.text for chunk in collected] == expected[:2]

    resumed = [
        chunk
        async for chunk in stream_facts(
            pipeline,
            "ignored",
            chunk_size=chunk_size,
            start_at=len(collected),
        )
    ]

    assert [chunk.index for chunk in resumed] == list(range(len(collected), len(expected)))
    assert [chunk.text for chunk in resumed] == expected[len(collected) :]

    assert [
        chunk
        async for chunk in stream_facts(pipeline, "ignored", chunk_size=chunk_size, start_at=10)
    ] == []
