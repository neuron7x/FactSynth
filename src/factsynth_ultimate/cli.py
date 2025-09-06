import json
import typer
import yaml
import os
from .generator import FSUInput, FSUConfig, generate_insight
from .metrics import j_index
from .orchestrator.roles import RoleConfig
from .orchestrator.pipeline import ProjectSpec, Orchestrator

app = typer.Typer(help="FactSynth Ultimate CLI")


@app.command()
def insight(intent: str, length: int = 100):
    print(generate_insight(FSUInput(intent=intent, length=length), FSUConfig()))


@app.command()
def score(intent: str, length: int = 100):
    cfg = FSUConfig()
    txt = generate_insight(FSUInput(intent=intent, length=length), cfg)
    print(txt, "\n---\n", j_index(intent, txt, cfg.start_phrase))


@app.command()
def glrtpm(
    spec: str = typer.Argument(..., help="YAML конфіг GLRTPM"), outdir: str = "./dist"
):
    os.makedirs(outdir, exist_ok=True)
    cfg = yaml.safe_load(open(spec, "r", encoding="utf-8"))
    roles = [RoleConfig(**r) for r in cfg["roles"]]
    ps = ProjectSpec(
        title=cfg["title"],
        thesis=cfg["thesis"],
        roles=roles,
        rounds=cfg.get("rounds", 2),
    )
    orch = Orchestrator(ps)
    res = orch.run()
    base = os.path.join(outdir, "tractate")
    open(base + ".md", "w", encoding="utf-8").write(res["markdown"])
    open(base + ".html", "w", encoding="utf-8").write(res["html"])
    open(
        base + ".metrics.json",
        "w",
        encoding="utf-8",
    ).write(json.dumps(res["metrics"], ensure_ascii=False, indent=2))
    print("OK →", outdir)


if __name__ == "__main__":
    app()
