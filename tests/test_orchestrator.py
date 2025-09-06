from src.factsynth_ultimate.orchestrator.roles import RoleConfig
from src.factsynth_ultimate.orchestrator.pipeline import ProjectSpec, Orchestrator

def test_glrtpm_pipeline_runs():
    spec = ProjectSpec(
        title="T", thesis="X",
        roles=[RoleConfig(name="R", goal="G", style="S", heuristics=["H"])],
        rounds=1
    )
    orch = Orchestrator(spec)
    res = orch.run()
    assert "markdown" in res and "metrics" in res and "html" in res
