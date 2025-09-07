from src.factsynth_ultimate.generator import (
    _resolve_valence,
    _process_seeds,
    _assemble_template,
    FSUInput,
    FSUConfig,
)


def test_resolve_valence_prefers_explicit():
    inp = FSUInput(intent="Test", valence="визнання")
    assert _resolve_valence(inp) == "визнання"


def test_process_seeds_extracts_unique_markers():
    inp = FSUInput(intent="I", facts=["Alpha Beta"], knowledge=["beta gamma", "delta1"])
    phrase = _process_seeds(inp)
    assert phrase == "Доменні маркери: alpha, beta, gamma."


def test_assemble_template_inserts_seed_phrase():
    cfg = FSUConfig()
    seed_phrase = "Доменні маркери: a."
    parts = _assemble_template(cfg, "новизна", "m", "c", "b", "h", "mtr", "d", seed_phrase)
    assert parts[5] == seed_phrase
    assert len(parts) == 11
