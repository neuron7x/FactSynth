import ast, json, subprocess, shutil, sys, os, textwrap
from pathlib import Path

SRC_DIR = os.path.join(os.getcwd(), "src")


def run_fsu(*args: str, **kwargs):
    env = kwargs.pop("env", os.environ.copy())
    env["PYTHONOPTIMIZE"] = "1"
    exe = shutil.which("fsu")
    if exe is not None:
        cmd = [exe, *args]
        kwargs["env"] = env
    else:
        cmd = [sys.executable, "-O", "-m", "factsynth_ultimate.cli", *args]
        env["PYTHONPATH"] = SRC_DIR
        kwargs["env"] = env
    return subprocess.run(cmd, **kwargs)


def test_fsu_score():
    r = run_fsu("score", "намір", "--length", "20", capture_output=True, text=True, timeout=20)
    assert r.returncode == 0
    assert "\n---\n" in r.stdout
    text_part, score_part = r.stdout.strip().split("\n---\n")
    assert text_part.strip()
    metrics = ast.literal_eval(score_part.strip())
    for key in ("F", "R", "D", "A", "N", "J"):
        assert key in metrics


def test_fsu_glrtpm(tmp_path: Path):
    spec = tmp_path / "spec.yaml"
    spec.write_text(
        textwrap.dedent(
            """
            title: T
            thesis: X
            roles:
              - name: R
                goal: G
                style: S
                heuristics: [H]
            rounds: 1
            """
        ).strip(),
        encoding="utf-8",
    )
    outdir = tmp_path / "out"
    r = run_fsu("glrtpm", str(spec), "--outdir", str(outdir), capture_output=True, text=True, timeout=20)
    assert r.returncode == 0
    assert f"OK → {outdir}" in r.stdout

    md = outdir / "tractate.md"
    html = outdir / "tractate.html"
    metrics_file = outdir / "tractate.metrics.json"
    assert md.is_file()
    assert html.is_file()
    assert metrics_file.is_file()

    metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    for key in ("coherence", "diversity", "contradiction"):
        assert key in metrics
