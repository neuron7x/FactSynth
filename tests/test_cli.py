import json
import subprocess
import sys


def test_cli_help():
    p = subprocess.run([sys.executable, "-m", "factsynth_ultimate", "-h"], capture_output=True, text=True)
    assert p.returncode == 0 and "FactSynth CLI" in p.stdout


def test_cli_gen():
    p = subprocess.run(
        [sys.executable, "-m", "factsynth_ultimate", "gen", "--prompt", "x y z", "--max-tokens", "2"],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0 and json.loads(p.stdout)["output"].startswith("x y |ck:")
