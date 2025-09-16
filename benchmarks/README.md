# Benchmark policy

The `bench` target runs the benchmark suite with [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/)
and stores machine readable results under `benchmarks/results/`. Thresholds for latency and throughput
regressions live in `thresholds.json`. The CI job fails when the measured latency exceeds the defined
maximum or the observed throughput drops below the configured minimum.

Generated artifacts (JSON + Markdown summary) are uploaded as a GitHub Actions artifact so the full
history of each run is available for review.

## Current regression limits

| Benchmark | Max latency (ms) | Min throughput (ops/s) |
| --- | --- | --- |
| `tests/benchmarks/test_retriever_benchmark.py::test_fixture_retriever_search_latency` | 4.0 | 250.0 |
