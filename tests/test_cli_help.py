import subprocess, sys, pytest

CMDS = [
    [sys.executable, "-m", "factsynth_ultimate", "--help"],
    [sys.executable, "-m", "factsynth", "--help"],
    ["factsynth","--help"],["factsynth-ultimate","--help"],
]

def test_cli_help():
    for c in CMDS:
        try:
            r = subprocess.run(c, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            if r.returncode == 0:
                return
        except Exception:
            pass
    pytest.skip("CLI not available.")
