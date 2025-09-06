from src.factsynth_ultimate.generator import generate_insight, FSUInput, FSUConfig
from src.factsynth_ultimate.tokenization import count_words

START = "Ти хочеш від мене…"

def test_contract_exact_length_and_prefix():
    cfg = FSUConfig()
    t = generate_insight(FSUInput(intent="Перевірка.", length=100), cfg)
    assert t.startswith(START)
    assert "?" not in t
    assert count_words(t) == 100
