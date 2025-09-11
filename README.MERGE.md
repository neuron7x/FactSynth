
# FactSynth Patch v2 — consolidated, deterministic, with QA tooling

- Adds: GLRTPM (/v1/glrtpm/run), AKP-SHI (/v1/akpshi/verify),
  LLM-IFC (/v1/llmifc/arbitrate), NDMACO, ISR (/v1/isr/*)
- Deterministic ISR (no stochastic noise); correct sampling rate handling.
- Tooling: ruff, black, mypy, pytest.ini, pre-commit; CI workflow.
- All packages include __init__.py
