from src.factsynth_ultimate.metrics import j_index
from src.factsynth_ultimate.generator import generate_insight, FSUInput, FSUConfig

def test_jindex_bounds():
    cfg = FSUConfig()
    intent = "Зменшити інформаційний шум, задати KPI, критерії та впровадити план"
    t = generate_insight(FSUInput(intent=intent, length=100), cfg)
    s = j_index(intent, t, cfg.start_phrase)
    assert 0.0 <= s["J"] <= 1.0
    for k in ["F","R","D","A","N","J"]:
        assert k in s
