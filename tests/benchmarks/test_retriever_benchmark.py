"""Benchmark coverage for the in-memory retriever implementation."""

from __future__ import annotations

import os
import random

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from factsynth_ultimate.services.retrievers.local import Fixture, LocalFixtureRetriever

pytestmark = pytest.mark.benchmark

RUN_BENCHMARKS = os.getenv("RUN_BENCHMARKS") == "1"

_FIXTURE_TEXT = """
Alpha is the first letter of the Greek alphabet.
Cloud native microservices scale globally within seconds.
Resilient architectures rely on redundant message passing and caching layers.
Machine learning pipelines monitor latency across inference clusters.
Distributed tracing provides observability into asynchronous workflows.
Compliance workloads validate personally identifiable information redaction.
Geospatial indexes accelerate proximity queries for logistics platforms.
High availability demands automated failover and rapid health checks.
Predictive maintenance models adapt to streaming telemetry data.
Cost optimization balances compute commitments with burstable workloads.
""".strip().splitlines()


@pytest.fixture(scope="module")
def retriever() -> LocalFixtureRetriever:
    random.seed(42)
    fixtures = []
    for idx in range(200):
        line = random.choice(_FIXTURE_TEXT)
        fixtures.append(Fixture(id=f"doc-{idx}", text=f"{line} #{idx}"))
    return LocalFixtureRetriever(fixtures)


@pytest.mark.skipif(not RUN_BENCHMARKS, reason="Benchmark suite disabled by default")
def test_fixture_retriever_search_latency(benchmark: BenchmarkFixture, retriever: LocalFixtureRetriever) -> None:
    query = "мікросервіси в хмарі з низькою латентністю"

    def run_search() -> list:
        return retriever.search(query, k=5)

    results = benchmark(run_search)
    assert results  # ensure the benchmark executed and returned fixtures
