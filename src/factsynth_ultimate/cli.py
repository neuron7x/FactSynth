import json, typer, yaml, os
from . import __version__
from .generator import FSUInput, FSUConfig, generate_insight
from .metrics import j_index
from .orchestrator.roles import RoleConfig
from .orchestrator.pipeline import ProjectSpec, Orchestrator

app = typer.Typer(help="FactSynth Ultimate CLI")


def _version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
):
    return

@app.command()
def insight(intent: str, length: int = 100):
    print(generate_insight(FSUInput(intent=intent, length=length), FSUConfig()))

@app.command()
def score(intent: str, length: int = 100):
    cfg = FSUConfig(); txt = generate_insight(FSUInput(intent=intent, length=length), cfg)
    print(txt, "\n---\n", j_index(intent, txt, cfg.start_phrase))

@app.command()
def glrtpm(spec: str = typer.Argument(..., help="YAML конфіг GLRTPM"), outdir: str = "./dist"):
    os.makedirs(outdir, exist_ok=True)
    cfg = yaml.safe_load(open(spec, "r", encoding="utf-8"))
    roles = [RoleConfig(**r) for r in cfg["roles"]]
    ps = ProjectSpec(title=cfg["title"], thesis=cfg["thesis"], roles=roles, rounds=cfg.get("rounds",2))
    orch = Orchestrator(ps); res = orch.run()
    base = os.path.join(outdir, "tractate")
    open(base+".md","w",encoding="utf-8").write(res["markdown"])
    open(base+".html","w",encoding="utf-8").write(res["html"])
    open(base+".metrics.json","w",encoding="utf-8").write(json.dumps(res["metrics"], ensure_ascii=False, indent=2))
    print("OK →", outdir)

if __name__ == "__main__":
    app()
